"""Redis connection and utilities."""

import logging
from typing import Optional, Any, List
import hashlib
import json

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis client
redis_client: Optional[Redis] = None


async def get_redis_client() -> Optional[Redis]:
    """Get Redis client instance."""
    global redis_client
    
    if redis_client is None:
        if not settings.REDIS_URL:
            logger.warning("Redis URL not configured, caching disabled")
            return None
            
        try:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,   # TCP_KEEPIDLE
                    2: 1,   # TCP_KEEPINTVL
                    3: 3,   # TCP_KEEPCNT
                }
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
                redis_client = None
                return None
    
    return redis_client


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Redis connection closed")


class RedisKeys:
    """Centralized Redis key patterns."""
    
    # Search related
    SEARCH_CACHE = "search:{user_id}:{query_hash}"
    SEARCH_SESSION = "search_session:{session_id}"
    SEARCH_CONTEXT = "search_context:{user_id}:{session_id}"
    QUERY_ANALYSIS = "query_analysis:{query_hash}"
    
    # User preferences
    USER_SEARCH_PREFS = "user:search_prefs:{user_id}"
    USER_SEARCH_HISTORY = "user:search_history:{user_id}"
    USER_CLICK_HISTORY = "user:clicks:{user_id}"
    
    # Embeddings cache
    EMBEDDING_CACHE = "embedding:{text_hash}"
    QUERY_EMBEDDING = "query_embedding:{query_hash}"
    
    # Analytics
    SEARCH_METRICS = "metrics:search:{date}"
    USER_BEHAVIOR = "behavior:{user_id}:{action_type}"
    SEARCH_FEEDBACK = "feedback:search:{search_id}"
    
    # Extension tokens (existing)
    EXTENSION_TOKEN = "extension_token:{token}"
    EXTENSION_TOKEN_ATTEMPTS = "extension_token_attempts:{email}"
    
    @staticmethod
    def hash_text(text: str) -> str:
        """Generate consistent hash for text."""
        return hashlib.md5(text.lower().encode()).hexdigest()[:12]


class CacheManager:
    """Utility class for managing cache operations."""
    
    def __init__(self):
        self.default_ttl = 3600  # 1 hour
        self.embedding_ttl = 86400 * 7  # 7 days for embeddings
        self.query_ttl = 3600  # 1 hour for query results
        
    async def get_or_set(
        self,
        key: str,
        fetch_func,
        ttl: Optional[int] = None,
        serialize: bool = True
    ):
        """
        Get value from cache or fetch and set if not exists.
        
        Args:
            key: Cache key
            fetch_func: Async function to fetch data if not in cache
            ttl: Time to live in seconds
            serialize: Whether to JSON serialize the value
            
        Returns:
            Cached or fetched value
        """
        redis_client = await get_redis_client()
        if not redis_client:
            # No cache available, just fetch
            return await fetch_func()
        
        try:
            # Try to get from cache
            cached = await redis_client.get(key)
            if cached:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(cached) if serialize else cached
            
            # Fetch and cache
            logger.debug(f"Cache miss for key: {key}")
            value = await fetch_func()
            
            # Store in cache
            cache_value = json.dumps(value) if serialize else str(value)
            await redis_client.setex(
                key,
                ttl or self.default_ttl,
                cache_value
            )
            
            return value
            
        except Exception as e:
            logger.error(f"Cache error for key {key}: {e}")
            # Fallback to fetching without cache
            return await fetch_func()
    
    async def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching a pattern.
        
        Args:
            pattern: Redis pattern (e.g., "search:user123:*")
        """
        redis_client = await get_redis_client()
        if not redis_client:
            return
        
        try:
            # Find all matching keys
            keys = []
            async for key in redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            # Delete in batches
            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
                
        except Exception as e:
            logger.error(f"Error invalidating cache pattern {pattern}: {e}")
    
    async def add_to_list(
        self,
        key: str,
        value: Any,
        max_length: int = 100,
        ttl: Optional[int] = None
    ):
        """Add value to a Redis list with max length."""
        redis_client = await get_redis_client()
        if not redis_client:
            return
        
        try:
            # Add to list
            await redis_client.lpush(key, json.dumps(value))
            
            # Trim to max length
            await redis_client.ltrim(key, 0, max_length - 1)
            
            # Set TTL if needed
            if ttl:
                await redis_client.expire(key, ttl)
                
        except Exception as e:
            logger.error(f"Error adding to list {key}: {e}")
    
    async def get_list(self, key: str, count: int = 10) -> List[Any]:
        """Get items from a Redis list."""
        redis_client = await get_redis_client()
        if not redis_client:
            return []
        
        try:
            items = await redis_client.lrange(key, 0, count - 1)
            return [json.loads(item) for item in items]
        except Exception as e:
            logger.error(f"Error getting list {key}: {e}")
            return []
    
    async def increment_counter(
        self,
        key: str,
        amount: int = 1,
        ttl: Optional[int] = None
    ) -> int:
        """Increment a counter in Redis."""
        redis_client = await get_redis_client()
        if not redis_client:
            return 0
        
        try:
            new_value = await redis_client.incrby(key, amount)
            
            if ttl:
                await redis_client.expire(key, ttl)
                
            return new_value
        except Exception as e:
            logger.error(f"Error incrementing counter {key}: {e}")
            return 0


# Global cache manager instance
cache_manager = CacheManager()