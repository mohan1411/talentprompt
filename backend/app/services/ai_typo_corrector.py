"""AI-powered typo correction service using GPT-4."""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
import asyncio
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)


class AITypoCorrector:
    """
    Intelligent typo correction using GPT-4 for context-aware corrections.
    Handles technical terms, industry jargon, and multi-language queries.
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = "gpt-4-turbo-preview"  # Fast model for typo correction
        self.cache_ttl = 86400  # 24 hours
        self.redis_client = None
        
    async def _get_redis(self):
        """Get Redis client lazily."""
        if not self.redis_client:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    async def correct_query(self, query: str, context: Optional[str] = "technical recruiting") -> Dict[str, Any]:
        """
        Correct typos in a query using AI with context awareness.
        
        Args:
            query: The query to correct
            context: Domain context (e.g., "technical recruiting", "healthcare")
            
        Returns:
            Dictionary with original, corrected query, and correction details
        """
        # Check cache first
        cached = await self._get_cached_correction(query)
        if cached:
            logger.info(f"Cache hit for typo correction: '{query}'")
            return cached
        
        # If no OpenAI key, use fallback correction
        if not self.client:
            logger.info("No OpenAI API key, using fallback typo correction")
            return await self._fallback_correction(query)
        
        try:
            # Build the correction prompt
            system_prompt = self._build_system_prompt(context)
            user_prompt = self._build_user_prompt(query)
            
            # Call GPT-4 for correction
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Validate and enhance result
            validated_result = self._validate_correction(query, result)
            
            # Cache the result
            await self._cache_correction(query, validated_result)
            
            return validated_result
            
        except Exception as e:
            logger.error(f"Error in AI typo correction: {e}")
            # Fallback to simple correction
            return await self._fallback_correction(query)
    
    def _build_system_prompt(self, context: str) -> str:
        """Build the system prompt for typo correction."""
        return f"""You are an expert at detecting and correcting typos in {context} search queries.

Your task is to:
1. Identify potential typos and misspellings
2. Correct them based on context
3. Handle technical terms, abbreviations, and industry jargon
4. Be aware of common keyboard typos and phonetic mistakes

Important rules:
- Only correct obvious typos, not intentional variations
- Preserve technical abbreviations that are correct (e.g., "JS" for JavaScript)
- Understand context (e.g., "AMS" likely means "AWS" in cloud computing context)
- Handle multi-word corrections (e.g., "java script" → "javascript")

Common technical corrections to be aware of:
- Programming languages: Python, JavaScript, TypeScript, Go, Rust, Java, C++, C#
- Frameworks: React, Angular, Vue, Django, Flask, Spring, Express
- Cloud: AWS, Azure, GCP, Docker, Kubernetes
- Databases: PostgreSQL, MySQL, MongoDB, Redis

Return a JSON object with this structure:
{{
    "corrected": "the corrected query",
    "corrections": [
        {{"from": "original word", "to": "corrected word", "confidence": 0.95, "reason": "typo"}}
    ],
    "confidence": 0.92,
    "has_corrections": true
}}

If no corrections needed, return has_corrections: false with empty corrections array."""
    
    def _build_user_prompt(self, query: str) -> str:
        """Build the user prompt for correction."""
        return f"""Please correct any typos in this search query: "{query}"

Consider the technical recruiting context. Common issues include:
- Keyboard typos (adjacent keys)
- Missing or extra letters
- Wrong capitalization
- Common misspellings of technical terms
- Abbreviation confusion (AMS → AWS, etc.)"""
    
    def _validate_correction(self, original: str, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the AI correction result."""
        # Ensure all required fields
        result = {
            "original": original,
            "corrected": ai_result.get("corrected", original),
            "corrections": ai_result.get("corrections", []),
            "confidence": ai_result.get("confidence", 0.0),
            "has_corrections": ai_result.get("has_corrections", False),
            "method": "ai"
        }
        
        # Validate corrections
        valid_corrections = []
        for correction in result["corrections"]:
            if all(key in correction for key in ["from", "to", "confidence"]):
                # Ensure the correction makes sense
                if correction["from"].lower() != correction["to"].lower():
                    valid_corrections.append(correction)
        
        result["corrections"] = valid_corrections
        result["has_corrections"] = len(valid_corrections) > 0
        
        # If no corrections were made, return original
        if not result["has_corrections"]:
            result["corrected"] = original
            result["confidence"] = 1.0
        
        return result
    
    async def _fallback_correction(self, query: str) -> Dict[str, Any]:
        """Simple fallback correction using pattern matching."""
        corrections = []
        words = query.split()
        corrected_words = []
        
        # Common technical typos
        common_typos = {
            "pythonn": "python",
            "pythoon": "python",
            "pyton": "python",
            "javscript": "javascript",
            "javascirpt": "javascript",
            "javascpt": "javascript",  # Common typo
            "javasript": "javascript",
            "javascrpt": "javascript",
            "javacript": "javascript",  # Another common typo
            "typscript": "typescript",
            "typescipt": "typescript",
            "kuberentes": "kubernetes",
            "kubernets": "kubernetes",
            "dokcer": "docker",
            "dockr": "docker",
            "ams": "aws",  # In tech context
            "amazone": "amazon",
            "gogle": "google",
            "googl": "google",
            "miscrosoft": "microsoft",
            "microsft": "microsoft"
        }
        
        for word in words:
            word_lower = word.lower()
            if word_lower in common_typos:
                corrected = common_typos[word_lower]
                corrections.append({
                    "from": word,
                    "to": corrected,
                    "confidence": 0.8,
                    "reason": "common_typo"
                })
                corrected_words.append(corrected)
            else:
                corrected_words.append(word)
        
        corrected_query = " ".join(corrected_words)
        
        return {
            "original": query,
            "corrected": corrected_query,
            "corrections": corrections,
            "confidence": 0.7 if corrections else 1.0,
            "has_corrections": len(corrections) > 0,
            "method": "fallback"
        }
    
    async def _get_cached_correction(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached correction if available."""
        try:
            redis = await self._get_redis()
            if not redis:
                return None
            
            cache_key = f"typo_correction:{query.lower()}"
            cached = await redis.get(cache_key)
            
            if cached:
                return json.loads(cached)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached correction: {e}")
            return None
    
    async def _cache_correction(self, query: str, result: Dict[str, Any]):
        """Cache correction result."""
        try:
            redis = await self._get_redis()
            if not redis:
                return
            
            cache_key = f"typo_correction:{query.lower()}"
            await redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(result)
            )
            
        except Exception as e:
            logger.error(f"Error caching correction: {e}")
    
    async def learn_from_feedback(self, original: str, user_correction: str):
        """Learn from user feedback on corrections."""
        # Store user corrections for future reference
        try:
            redis = await self._get_redis()
            if not redis:
                return
            
            # Store in a feedback set
            feedback_key = f"typo_feedback:{original.lower()}"
            await redis.setex(
                feedback_key,
                self.cache_ttl * 30,  # Keep for 30 days
                user_correction
            )
            
            # Invalidate cache for this query
            cache_key = f"typo_correction:{original.lower()}"
            await redis.delete(cache_key)
            
            logger.info(f"Learned correction: '{original}' → '{user_correction}'")
            
        except Exception as e:
            logger.error(f"Error storing feedback: {e}")


# Singleton instance
ai_typo_corrector = AITypoCorrector()