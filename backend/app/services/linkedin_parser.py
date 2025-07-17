"""LinkedIn profile parser service."""

import re
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from openai import AsyncOpenAI

from app.core.config import settings

try:
    from app.services.search_skill_fix import (
        normalize_skill_for_storage,
        extract_skills_from_text
    )
except ImportError:
    # Fallback if module not available
    def normalize_skill_for_storage(skill):
        return skill.strip()
    
    def extract_skills_from_text(text):
        return []

logger = logging.getLogger(__name__)


class LinkedInParser:
    """Service for parsing LinkedIn profile data."""
    
    def __init__(self):
        """Initialize the LinkedIn parser."""
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
    
    async def parse_linkedin_data(self, profile_data: Dict[str, Any], use_ai: bool = True) -> Dict[str, Any]:
        """Parse LinkedIn profile data into structured format.
        
        Args:
            profile_data: Raw LinkedIn profile data from Chrome extension
            use_ai: Whether to use AI for parsing (requires OpenAI API key)
            
        Returns:
            Parsed and structured data
        """
        # Try AI parsing first if available and we have full_text
        if use_ai and self.client and profile_data.get("full_text"):
            try:
                logger.info("Using AI to parse LinkedIn profile")
                ai_parsed = await self._parse_with_ai(profile_data)
                if ai_parsed:
                    return ai_parsed
            except Exception as e:
                logger.error(f"AI parsing failed, falling back to rule-based: {str(e)}")
        
        # Fallback to rule-based parsing
        logger.info("Using rule-based parsing for LinkedIn profile")
        parsed = {
            "first_name": "",
            "last_name": "",
            "email": profile_data.get("email", ""),  # Use email from Chrome extension if provided
            "phone": profile_data.get("phone", ""),  # Use phone from Chrome extension if provided
            "years_experience": 0,
            "keywords": [],
            "raw_text": "",
            "education": [],
            "experience": [],
            "certifications": [],
            "languages": [],
            "parsed_at": datetime.utcnow().isoformat()
        }
        
        # Parse name
        if profile_data.get("name"):
            name_parts = self._parse_name(profile_data["name"])
            parsed["first_name"] = name_parts["first_name"]
            parsed["last_name"] = name_parts["last_name"]
        
        # Calculate years of experience
        if profile_data.get("experience"):
            parsed["years_experience"] = self._calculate_experience_years(
                profile_data["experience"]
            )
            parsed["experience"] = self._parse_experience(profile_data["experience"])
        
        # Parse education
        if profile_data.get("education"):
            parsed["education"] = self._parse_education(profile_data["education"])
        
        # Normalize skills in profile data
        if profile_data.get("skills"):
            profile_data["skills"] = [normalize_skill_for_storage(skill) for skill in profile_data["skills"]]
        
        # Extract keywords
        parsed["keywords"] = self._extract_keywords(profile_data)
        
        # Build raw text for search
        parsed["raw_text"] = profile_data.get("full_text") or self._build_raw_text(profile_data)
        
        return parsed
    
    def _parse_name(self, full_name: str) -> Dict[str, str]:
        """Parse full name into first and last name."""
        parts = full_name.strip().split()
        
        if len(parts) == 0:
            return {"first_name": "", "last_name": ""}
        elif len(parts) == 1:
            return {"first_name": parts[0], "last_name": ""}
        elif len(parts) == 2:
            return {"first_name": parts[0], "last_name": parts[1]}
        else:
            # Handle middle names, suffixes, etc.
            # Assume first word is first name, rest is last name
            return {"first_name": parts[0], "last_name": " ".join(parts[1:])}
    
    def _calculate_experience_years(self, experiences: List[Dict]) -> int:
        """Calculate total years of experience from experience list."""
        total_months = 0
        
        for exp in experiences:
            duration = exp.get("duration", "")
            if not duration:
                continue
            
            # Extract years and months from duration string
            # Examples: "2 years 3 months", "1 year", "6 months", "11 yrs 7 mos"
            years_match = re.search(r'(\d+)\s*(?:year|yr)', duration, re.I)
            months_match = re.search(r'(\d+)\s*(?:month|mo)', duration, re.I)
            
            years = int(years_match.group(1)) if years_match else 0
            months = int(months_match.group(1)) if months_match else 0
            
            total_months += (years * 12) + months
            
            # Log for debugging
            if years or months:
                logger.debug(f"Experience duration '{duration}' = {years} years, {months} months")
        
        # Convert to years (rounded to nearest)
        total_years = round(total_months / 12)
        logger.info(f"Total experience calculated: {total_years} years from {total_months} months")
        return total_years
    
    def _parse_experience(self, experiences: List[Dict]) -> List[Dict]:
        """Parse experience entries."""
        parsed_experiences = []
        
        for exp in experiences:
            parsed_exp = {
                "title": exp.get("title", ""),
                "company": exp.get("company", ""),
                "location": exp.get("location", ""),
                "duration": exp.get("duration", ""),
                "description": exp.get("description", ""),
                "start_date": self._extract_date(exp.get("duration", ""), "start"),
                "end_date": self._extract_date(exp.get("duration", ""), "end"),
                "is_current": self._is_current_position(exp.get("duration", ""))
            }
            parsed_experiences.append(parsed_exp)
        
        return parsed_experiences
    
    def _parse_education(self, education: List[Dict]) -> List[Dict]:
        """Parse education entries."""
        parsed_education = []
        
        for edu in education:
            parsed_edu = {
                "school": edu.get("school", ""),
                "degree": edu.get("degree", ""),
                "field": edu.get("field", ""),
                "year": edu.get("year", ""),
                "activities": edu.get("activities", ""),
                "description": edu.get("description", "")
            }
            parsed_education.append(parsed_edu)
        
        return parsed_education
    
    def _extract_keywords(self, profile_data: Dict[str, Any]) -> List[str]:
        """Extract keywords from profile data."""
        keywords = []
        
        # Add skills as keywords (normalized)
        if profile_data.get("skills"):
            normalized_skills = [normalize_skill_for_storage(skill) for skill in profile_data["skills"]]
            keywords.extend(normalized_skills)
        
        # Extract keywords from headline
        if profile_data.get("headline"):
            # Common job titles and technologies
            headline_keywords = re.findall(
                r'\b(?:Engineer|Developer|Manager|Director|Lead|Senior|Junior|'
                r'Architect|Designer|Analyst|Consultant|Specialist|Expert|'
                r'Python|Java|JavaScript|React|Node|AWS|Azure|Docker|Kubernetes|'
                r'Machine Learning|AI|Data Science|DevOps|Cloud|Mobile|Web|'
                r'Frontend|Backend|Full Stack|Fullstack)\b',
                profile_data["headline"],
                re.I
            )
            keywords.extend([kw.title() for kw in headline_keywords])
        
        # Extract from experience
        if profile_data.get("experience"):
            for exp in profile_data["experience"]:
                if exp.get("title"):
                    title_keywords = re.findall(
                        r'\b(?:Engineer|Developer|Manager|Lead|Senior|Junior)\b',
                        exp["title"],
                        re.I
                    )
                    keywords.extend([kw.title() for kw in title_keywords])
        
        # Remove duplicates and return
        return list(set(keywords))
    
    def _build_raw_text(self, profile_data: Dict[str, Any]) -> str:
        """Build searchable raw text from profile data."""
        text_parts = []
        
        # Add name
        if profile_data.get("name"):
            text_parts.append(profile_data["name"])
        
        # Add headline
        if profile_data.get("headline"):
            text_parts.append(profile_data["headline"])
        
        # Add location
        if profile_data.get("location"):
            text_parts.append(profile_data["location"])
        
        # Add about/summary
        if profile_data.get("about"):
            text_parts.append(profile_data["about"])
        
        # Add experience
        if profile_data.get("experience"):
            for exp in profile_data["experience"]:
                exp_text = f"{exp.get('title', '')} at {exp.get('company', '')} {exp.get('description', '')}"
                text_parts.append(exp_text)
        
        # Add education
        if profile_data.get("education"):
            for edu in profile_data["education"]:
                edu_text = f"{edu.get('degree', '')} {edu.get('field', '')} from {edu.get('school', '')}"
                text_parts.append(edu_text)
        
        # Add skills (normalized)
        if profile_data.get("skills"):
            normalized_skills = [normalize_skill_for_storage(skill) for skill in profile_data["skills"]]
            text_parts.append(" ".join(normalized_skills))
        
        return "\n\n".join(text_parts)
    
    def _extract_date(self, duration_str: str, date_type: str) -> Optional[str]:
        """Extract start or end date from duration string."""
        # This is a simplified implementation
        # Real implementation would parse actual dates from duration
        return None
    
    def _is_current_position(self, duration_str: str) -> bool:
        """Check if position is current based on duration string."""
        return "present" in duration_str.lower() or "current" in duration_str.lower()
    
    async def _parse_with_ai(self, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse LinkedIn profile using AI (OpenAI).
        
        Args:
            profile_data: LinkedIn profile data with full_text field
            
        Returns:
            Parsed profile data or None if parsing fails
        """
        if not profile_data.get("full_text"):
            return None
        
        system_prompt = """You are an expert LinkedIn profile parser. Extract structured information from the LinkedIn profile text.

IMPORTANT: Ignore any content about other people (like "Narendra Modi", "Jeff Weiner", followers, etc.) - focus ONLY on the profile owner's information.

Return a JSON object with the following structure:
{
    "first_name": "string",
    "last_name": "string",
    "email": "string or null",
    "phone": "string or null",
    "location": "string or null",
    "current_title": "string (job title/headline)",
    "summary": "string (about section)",
    "years_experience": number (calculate total years from ALL experience durations),
    "keywords": ["list", "of", "relevant", "keywords"],
    "skills": ["list", "of", "skills", "(normalize: websphere -> WebSphere, etc.)"],
    "experience": [
        {
            "title": "Job Title",
            "company": "Company Name",
            "location": "Location or null",
            "duration": "Date range as shown (e.g., 'Jan 2014 - Present · 11 yrs 7 mos')",
            "description": "Job description or null",
            "is_current": boolean
        }
    ],
    "education": [
        {
            "degree": "Degree type",
            "field": "Field of study",
            "school": "Institution name",
            "dates": "Date range or graduation year",
            "activities": "Activities or null"
        }
    ],
    "certifications": ["list of certifications if any"],
    "languages": ["list of languages if mentioned"]
}

Important:
- Extract ALL experience entries, don't skip any
- Calculate years_experience by adding up all durations (e.g., "11 yrs 7 mos" + "6 yrs 3 mos" = ~18 years)
- Ignore endorsement numbers, follower counts, and references to other people
- Set is_current to true if the position shows "Present" in the date range
- Keep the full duration string exactly as shown"""
        
        user_prompt = f"""Parse this LinkedIn profile:

{profile_data.get('full_text', '')}

Additional structured data if available:
Name: {profile_data.get('name', '')}
Headline: {profile_data.get('headline', '')}
Location: {profile_data.get('location', '')}
Email: {profile_data.get('email', '') or 'Not provided'}
Phone: {profile_data.get('phone', '') or 'Not provided'}
About: {profile_data.get('about', '')[:500] if profile_data.get('about') else ''}
Skills: {', '.join([normalize_skill_for_storage(s) for s in profile_data.get('skills', [])[:20]])}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            parsed = json.loads(response.choices[0].message.content)
            
            # Normalize skills
            if parsed.get("skills"):
                parsed["skills"] = [normalize_skill_for_storage(skill) for skill in parsed["skills"]]
            
            # Add metadata
            parsed["parsed_at"] = datetime.utcnow().isoformat()
            parsed["raw_text"] = profile_data.get("full_text", "")
            parsed["parsing_method"] = "ai"
            
            # Ensure required fields exist and preserve email/phone from Chrome extension
            parsed.setdefault("email", profile_data.get("email", ""))
            parsed.setdefault("phone", profile_data.get("phone", ""))
            parsed.setdefault("certifications", [])
            parsed.setdefault("languages", [])
            
            # Override with Chrome extension data if AI didn't find them
            if not parsed.get("email") and profile_data.get("email"):
                parsed["email"] = profile_data.get("email")
            if not parsed.get("phone") and profile_data.get("phone"):
                parsed["phone"] = profile_data.get("phone")
            
            logger.info(f"Successfully parsed LinkedIn profile with AI: {parsed.get('first_name')} {parsed.get('last_name')}")
            return parsed
            
        except Exception as e:
            logger.error(f"AI parsing error: {str(e)}")
            return None