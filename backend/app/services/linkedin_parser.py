"""LinkedIn profile parser service."""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LinkedInParser:
    """Service for parsing LinkedIn profile data."""
    
    async def parse_linkedin_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LinkedIn profile data into structured format.
        
        Args:
            profile_data: Raw LinkedIn profile data from Chrome extension
            
        Returns:
            Parsed and structured data
        """
        parsed = {
            "first_name": "",
            "last_name": "",
            "email": "",  # LinkedIn doesn't expose email
            "phone": "",  # LinkedIn doesn't expose phone
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
        
        # Extract keywords
        parsed["keywords"] = self._extract_keywords(profile_data)
        
        # Build raw text for search
        parsed["raw_text"] = self._build_raw_text(profile_data)
        
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
            # Examples: "2 years 3 months", "1 year", "6 months"
            years_match = re.search(r'(\d+)\s*year', duration, re.I)
            months_match = re.search(r'(\d+)\s*month', duration, re.I)
            
            years = int(years_match.group(1)) if years_match else 0
            months = int(months_match.group(1)) if months_match else 0
            
            total_months += (years * 12) + months
        
        # Convert to years (rounded down)
        return total_months // 12
    
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
        
        # Add skills as keywords
        if profile_data.get("skills"):
            keywords.extend(profile_data["skills"])
        
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
        
        # Add skills
        if profile_data.get("skills"):
            text_parts.append(" ".join(profile_data["skills"]))
        
        return "\n\n".join(text_parts)
    
    def _extract_date(self, duration_str: str, date_type: str) -> Optional[str]:
        """Extract start or end date from duration string."""
        # This is a simplified implementation
        # Real implementation would parse actual dates from duration
        return None
    
    def _is_current_position(self, duration_str: str) -> bool:
        """Check if position is current based on duration string."""
        return "present" in duration_str.lower() or "current" in duration_str.lower()