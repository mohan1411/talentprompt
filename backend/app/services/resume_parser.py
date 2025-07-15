"""AI-powered resume parsing service."""

import json
import logging
import re
from typing import Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class ResumeParser:
    """Service for parsing resume content using AI."""
    
    def __init__(self):
        """Initialize the resume parser."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL  # Using gpt-4o-mini for better performance and cost efficiency
    
    async def parse_resume(self, text: str) -> Dict:
        """Parse resume text using OpenAI to extract structured data.
        
        Args:
            text: Raw resume text
            
        Returns:
            Dictionary containing parsed resume data
        """
        system_prompt = """You are an expert resume parser. Extract the following information from the resume text and return it as a JSON object:

{
    "first_name": "string",
    "last_name": "string", 
    "email": "string or null",
    "phone": "string or null",
    "location": "string or null",
    "current_title": "string or null",
    "summary": "string or null (professional summary/objective)",
    "years_experience": "number or null (total years of experience)",
    "skills": ["list", "of", "skills"],
    "keywords": ["important", "keywords", "from", "resume"],
    "education": [
        {
            "degree": "string",
            "field": "string",
            "institution": "string",
            "year": "string or null"
        }
    ],
    "experience": [
        {
            "title": "string",
            "company": "string",
            "duration": "string",
            "description": "string"
        }
    ]
}

Important:
- Extract actual data, don't make up information
- For years_experience, calculate based on work history if not explicitly stated
- Skills should be technical skills, tools, technologies mentioned
- Keywords should include important terms for search (technologies, roles, industries)
- If information is not found, use null
- Clean and standardize phone numbers and emails"""

        user_prompt = f"Parse this resume:\n\n{text[:4000]}"  # Limit text to avoid token limits
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            parsed_data = json.loads(content)
            
            # Validate and clean the parsed data
            return self._validate_parsed_data(parsed_data)
            
        except Exception as e:
            logger.error(f"Error parsing resume with AI: {e}")
            # Return basic extraction as fallback
            return self._basic_extraction(text)
    
    def _validate_parsed_data(self, data: Dict) -> Dict:
        """Validate and clean parsed resume data."""
        # Ensure required fields exist
        validated = {
            "first_name": data.get("first_name", "Unknown"),
            "last_name": data.get("last_name", "Unknown"),
            "email": self._clean_email(data.get("email")),
            "phone": self._clean_phone(data.get("phone")),
            "location": data.get("location"),
            "current_title": data.get("current_title"),
            "summary": data.get("summary"),
            "years_experience": self._clean_years_experience(data.get("years_experience")),
            "skills": data.get("skills", []),
            "keywords": data.get("keywords", []),
            "education": data.get("education", []),
            "experience": data.get("experience", [])
        }
        
        # Ensure skills and keywords are lists
        if not isinstance(validated["skills"], list):
            validated["skills"] = []
        if not isinstance(validated["keywords"], list):
            validated["keywords"] = []
        
        # Limit array sizes
        validated["skills"] = validated["skills"][:50]
        validated["keywords"] = validated["keywords"][:30]
        
        return validated
    
    def _clean_email(self, email: Optional[str]) -> Optional[str]:
        """Clean and validate email."""
        if not email:
            return None
        
        # Basic email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email):
            return email.lower()
        return None
    
    def _clean_phone(self, phone: Optional[str]) -> Optional[str]:
        """Clean phone number."""
        if not phone:
            return None
        
        # Remove all non-numeric characters
        cleaned = re.sub(r'[^\d+]', '', phone)
        if len(cleaned) >= 10:
            return cleaned
        return None
    
    def _clean_years_experience(self, years: any) -> Optional[int]:
        """Clean years of experience."""
        if years is None:
            return None
        
        try:
            years_int = int(years)
            if 0 <= years_int <= 50:
                return years_int
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _basic_extraction(self, text: str) -> Dict:
        """Basic extraction fallback when AI parsing fails."""
        lines = text.split('\n')
        
        # Try to extract name from first few lines
        name_parts = []
        for line in lines[:5]:
            words = line.strip().split()
            if 2 <= len(words) <= 4 and all(word.isalpha() for word in words):
                name_parts = words
                break
        
        first_name = name_parts[0] if name_parts else "Unknown"
        last_name = name_parts[-1] if len(name_parts) > 1 else "Unknown"
        
        # Extract email
        email = None
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if email_match:
            email = email_match.group(0).lower()
        
        # Extract phone
        phone = None
        phone_match = re.search(r'[\+\d]?[\d\s\-\(\)]{10,}', text)
        if phone_match:
            phone = re.sub(r'[^\d+]', '', phone_match.group(0))
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "location": None,
            "current_title": None,
            "summary": None,
            "years_experience": None,
            "skills": [],
            "keywords": [],
            "education": [],
            "experience": []
        }


# Singleton instance
resume_parser = ResumeParser()