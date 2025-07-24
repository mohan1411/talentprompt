"""Extension token service for OAuth user authentication."""

import logging
import secrets
import string
from typing import Optional

from app.core.config import settings
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)


class ExtensionTokenService:
    """Service for managing extension access tokens."""
    
    def __init__(self):
        self.token_length = settings.EXTENSION_TOKEN_LENGTH
        self.expire_seconds = settings.EXTENSION_TOKEN_EXPIRE_SECONDS
        self.rate_limit = settings.EXTENSION_TOKEN_RATE_LIMIT
        # Exclude confusing characters (0, O, I, l, 1)
        self.charset = string.ascii_uppercase.replace('O', '').replace('I', '') + \
                      string.digits.replace('0', '').replace('1', '')
    
    async def generate_token(self, email: str) -> Optional[str]:
        """Generate a new access token for the user."""
        try:
            # Check rate limit
            if not await self._check_rate_limit(email):
                logger.warning(f"Rate limit exceeded for {email}")
                return None
            
            # Generate token
            token = ''.join(secrets.choice(self.charset) for _ in range(self.token_length))
            
            # Store in Redis
            redis = await get_redis_client()
            key = f"ext_token:{email}"
            
            # Delete any existing token
            await redis.delete(key)
            
            # Set new token with expiration
            await redis.setex(key, self.expire_seconds, token)
            
            # Update rate limit counter
            await self._update_rate_limit(email)
            
            logger.info(f"Generated extension token for {email}")
            return token
            
        except Exception as e:
            logger.error(f"Error generating token for {email}: {e}")
            return None
    
    async def verify_token(self, email: str, token: str, consume: bool = True) -> bool:
        """Verify if the provided token is valid for the user.
        
        Args:
            email: User's email
            token: Token to verify
            consume: If True, delete token after successful verification (one-time use)
        """
        try:
            redis = await get_redis_client()
            key = f"ext_token:{email}"
            
            # Get stored token
            stored_token = await redis.get(key)
            
            # Handle bytes response from Redis
            if isinstance(stored_token, bytes):
                stored_token = stored_token.decode('utf-8')
            
            logger.info(f"Token verification for {email}: provided='{token}', stored='{stored_token}', consume={consume}")
            
            if not stored_token:
                logger.debug(f"No token found for {email}")
                return False
            
            # Case-insensitive comparison for better UX
            if stored_token.upper() == token.upper():
                if consume:
                    # Delete token after successful use (one-time use)
                    await redis.delete(key)
                    logger.info(f"Token verified and consumed for {email}")
                else:
                    logger.info(f"Token verified (not consumed) for {email}")
                return True
            
            # Update failed attempts
            await self._update_failed_attempts(email)
            logger.warning(f"Invalid token attempted for {email}: '{token}' != '{stored_token}'")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying token for {email}: {e}")
            return False
    
    async def get_token_status(self, email: str) -> dict:
        """Get the current token status for a user."""
        try:
            redis = await get_redis_client()
            key = f"ext_token:{email}"
            
            # Check if token exists
            exists = await redis.exists(key)
            
            if not exists:
                return {
                    "has_token": False,
                    "ttl": 0
                }
            
            # Get TTL
            ttl = await redis.ttl(key)
            
            return {
                "has_token": True,
                "ttl": max(0, ttl)
            }
            
        except Exception as e:
            logger.error(f"Error checking token status for {email}: {e}")
            return {
                "has_token": False,
                "ttl": 0,
                "error": str(e)
            }
    
    async def revoke_token(self, email: str) -> bool:
        """Revoke any existing token for the user."""
        try:
            redis = await get_redis_client()
            key = f"ext_token:{email}"
            
            deleted = await redis.delete(key)
            
            if deleted:
                logger.info(f"Token revoked for {email}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error revoking token for {email}: {e}")
            return False
    
    async def _check_rate_limit(self, email: str) -> bool:
        """Check if user is within rate limit."""
        try:
            redis = await get_redis_client()
            key = f"ext_token_rate:{email}"
            
            count = await redis.get(key)
            if count and int(count) >= self.rate_limit:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # Allow on error
            return True
    
    async def _update_rate_limit(self, email: str):
        """Update rate limit counter."""
        try:
            redis = await get_redis_client()
            key = f"ext_token_rate:{email}"
            
            # Increment counter
            count = await redis.incr(key)
            
            # Set expiration on first increment
            if count == 1:
                await redis.expire(key, 3600)  # 1 hour
                
        except Exception as e:
            logger.error(f"Error updating rate limit: {e}")
    
    async def _update_failed_attempts(self, email: str):
        """Track failed token attempts."""
        try:
            redis = await get_redis_client()
            key = f"ext_token_fails:{email}"
            
            # Increment counter
            count = await redis.incr(key)
            
            # Set expiration on first increment
            if count == 1:
                await redis.expire(key, 3600)  # 1 hour
            
            # Log if too many failures
            if count > 5:
                logger.warning(f"Multiple failed token attempts for {email}: {count}")
                
        except Exception as e:
            logger.error(f"Error tracking failed attempts: {e}")


# Global instance
extension_token_service = ExtensionTokenService()