"""Redis connection and utilities."""

import logging
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis client
redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    """Get Redis client instance."""
    global redis_client
    
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await redis_client.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # For development, we'll create a fake Redis client that stores in memory
            # In production, this should raise an error
            if settings.DEBUG:
                logger.warning("Using in-memory cache fallback for development")
                from app.core.cache_fallback import InMemoryCache
                redis_client = InMemoryCache()
            else:
                raise
    
    return redis_client


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Redis connection closed")