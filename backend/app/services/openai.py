"""OpenAI service for AI-powered features."""

import json
import logging
from typing import List, Dict, Any, Optional
import asyncio
from functools import lru_cache

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API.
    
    Currently using GPT-4o-mini as the primary model for:
    - 98% cost reduction compared to GPT-4-turbo
    - Excellent performance for recruitment tasks
    - Low latency for real-time operations
    """
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        self.model = settings.OPENAI_MODEL  # gpt-4o-mini by default
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def generate_completion(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        response_format: Optional[str] = "json"
    ) -> str:
        """Generate a completion using OpenAI API."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert AI assistant helping with recruitment and HR tasks. Always provide structured, professional responses."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Add response format if specified
            if response_format == "json":
                payload["response_format"] = {"type": "json_object"}
                messages[0]["content"] += " Always respond with valid JSON."
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"OpenAI API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise
    
    async def generate_embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small"
    ) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        try:
            # OpenAI has a limit of 8191 tokens per request
            # Split texts into batches if needed
            embeddings = []
            batch_size = 100  # Process 100 texts at a time
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = await self.client.post(
                    f"{self.base_url}/embeddings",
                    json={
                        "input": batch,
                        "model": model
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                batch_embeddings = [item["embedding"] for item in result["data"]]
                embeddings.extend(batch_embeddings)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    async def analyze_resume_content(
        self,
        resume_text: str,
        job_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze resume content and extract key information."""
        prompt = f"""
        Analyze the following resume and extract key information.
        
        Resume:
        {resume_text[:3000]}  # Limit to avoid token limits
        
        {"Job Description: " + job_description if job_description else ""}
        
        Extract and return as JSON:
        1. Skills (technical and soft skills)
        2. Years of experience
        3. Education summary
        4. Key achievements
        5. Industry/domain expertise
        6. Strengths
        7. Potential concerns or gaps
        {f"8. Match score with job description (0-100)" if job_description else ""}
        
        Be thorough but concise.
        """
        
        try:
            response = await self.generate_completion(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error analyzing resume: {e}")
            return {
                "skills": [],
                "years_experience": 0,
                "education": "Not available",
                "achievements": [],
                "expertise": [],
                "strengths": [],
                "concerns": [],
                "match_score": 0 if job_description else None
            }
    
    async def generate_search_suggestions(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate search query suggestions based on user input."""
        prompt = f"""
        Based on the search query: "{query}"
        {f"Context: {json.dumps(context)}" if context else ""}
        
        Generate 5 relevant search suggestions for finding candidates.
        These should be natural language queries that expand on or refine the original query.
        
        Return as JSON array of strings.
        """
        
        try:
            response = await self.generate_completion(prompt, temperature=0.8)
            suggestions = json.loads(response)
            return suggestions[:5]  # Ensure we return max 5
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
@lru_cache()
def get_openai_service() -> OpenAIService:
    """Get or create OpenAI service instance."""
    return OpenAIService()


# For direct import
openai_service = get_openai_service()