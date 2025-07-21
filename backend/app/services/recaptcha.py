"""Google reCAPTCHA v3 verification service."""

import httpx
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
RECAPTCHA_THRESHOLD = 0.5  # Minimum score to consider valid


class RecaptchaService:
    """Service for verifying Google reCAPTCHA v3 tokens."""
    
    @staticmethod
    async def verify_token(token: str, action: Optional[str] = None) -> bool:
        """
        Verify a reCAPTCHA token.
        
        Args:
            token: The reCAPTCHA token from the client
            action: Optional action name to verify
            
        Returns:
            True if the token is valid and score is above threshold
        """
        # Skip verification if disabled
        if not settings.RECAPTCHA_ENABLED or not settings.RECAPTCHA_SECRET_KEY:
            logger.warning("reCAPTCHA verification skipped - not configured")
            return True
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    RECAPTCHA_VERIFY_URL,
                    data={
                        "secret": settings.RECAPTCHA_SECRET_KEY,
                        "response": token
                    }
                )
                
                result = response.json()
                
                # Check if verification was successful
                if not result.get("success", False):
                    logger.warning(f"reCAPTCHA verification failed: {result.get('error-codes', [])}")
                    return False
                    
                # Check score (v3 specific)
                score = result.get("score", 0)
                if score < RECAPTCHA_THRESHOLD:
                    logger.warning(f"reCAPTCHA score too low: {score}")
                    return False
                    
                # Check action if provided
                if action and result.get("action") != action:
                    logger.warning(f"reCAPTCHA action mismatch: expected {action}, got {result.get('action')}")
                    return False
                    
                logger.info(f"reCAPTCHA verification successful - score: {score}")
                return True
                
        except Exception as e:
            logger.error(f"reCAPTCHA verification error: {str(e)}")
            # Fail open - allow registration if reCAPTCHA service is down
            return True


recaptcha_service = RecaptchaService()