"""Embedding generation service using OpenAI."""

import logging
from typing import List, Optional

import openai
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        """Initialize the embedding service."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "text-embedding-ada-002"
        self.max_tokens = 8191  # Max tokens for ada-002
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text.
        
        Args:
            text: The text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return None
        
        try:
            # Truncate text if too long (rough estimation: 1 token ≈ 4 chars)
            if len(text) > self.max_tokens * 4:
                text = text[:self.max_tokens * 4]
                logger.info("Text truncated for embedding generation")
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=text.strip()
            )
            
            embedding = response.data[0].embedding
            return embedding
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {e}")
            return None
    
    async def generate_embeddings_batch(
        self, texts: List[str]
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors (or None for failed items)
        """
        embeddings = []
        
        # OpenAI allows batch processing, but we'll process one by one
        # to handle errors gracefully
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    def prepare_resume_text(self, resume_data: dict) -> str:
        """Prepare resume data for embedding generation.
        
        Combines relevant fields into a single text representation.
        
        Args:
            resume_data: Dictionary containing resume information
            
        Returns:
            Formatted text for embedding
        """
        parts = []
        
        # Add basic info
        if resume_data.get("first_name") and resume_data.get("last_name"):
            parts.append(f"{resume_data['first_name']} {resume_data['last_name']}")
        
        if resume_data.get("current_title"):
            parts.append(f"Title: {resume_data['current_title']}")
        
        if resume_data.get("location"):
            parts.append(f"Location: {resume_data['location']}")
        
        if resume_data.get("years_experience"):
            parts.append(f"Experience: {resume_data['years_experience']} years")
        
        # Add summary
        if resume_data.get("summary"):
            parts.append(f"Summary: {resume_data['summary']}")
        
        # Add skills
        if resume_data.get("skills"):
            skills_text = ", ".join(resume_data["skills"])
            parts.append(f"Skills: {skills_text}")
        
        # Add raw text if available (but limit length)
        if resume_data.get("raw_text"):
            # Take first 2000 chars of raw text to avoid token limits
            raw_excerpt = resume_data["raw_text"][:2000]
            parts.append(f"Resume Content: {raw_excerpt}")
        
        return "\n\n".join(parts)


# Singleton instance
embedding_service = EmbeddingService()