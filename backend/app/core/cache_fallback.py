"""In-memory cache fallback for development when Redis is not available."""

import asyncio
from typing import Any, Dict, Optional
from datetime import datetime, timedelta


class InMemoryCache:
    """Simple in-memory cache that mimics Redis interface."""
    
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._expiry: Dict[str, datetime] = {}
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        self._cleanup_expired()
        if key in self._store and key not in self._expiry:
            return self._store[key]
        if key in self._expiry and datetime.now() < self._expiry[key]:
            return self._store[key]
        return None
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set key-value with optional expiration in seconds."""
        self._store[key] = value
        if ex:
            self._expiry[key] = datetime.now() + timedelta(seconds=ex)
        return True
    
    async def setex(self, key: str, seconds: int, value: str) -> bool:
        """Set key-value with expiration."""
        return await self.set(key, value, ex=seconds)
    
    async def delete(self, key: str) -> int:
        """Delete key."""
        deleted = 0
        if key in self._store:
            del self._store[key]
            deleted = 1
        if key in self._expiry:
            del self._expiry[key]
        return deleted
    
    async def exists(self, key: str) -> int:
        """Check if key exists."""
        self._cleanup_expired()
        if key in self._store:
            if key not in self._expiry or datetime.now() < self._expiry[key]:
                return 1
        return 0
    
    async def incr(self, key: str) -> int:
        """Increment integer value."""
        current = await self.get(key)
        if current is None:
            value = 1
        else:
            value = int(current) + 1
        await self.set(key, str(value))
        return value
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on existing key."""
        if key in self._store:
            self._expiry[key] = datetime.now() + timedelta(seconds=seconds)
            return True
        return False
    
    async def ttl(self, key: str) -> int:
        """Get time to live in seconds."""
        if key not in self._expiry:
            return -1
        
        ttl = (self._expiry[key] - datetime.now()).total_seconds()
        if ttl <= 0:
            return -2
        return int(ttl)
    
    async def ping(self) -> bool:
        """Test connection."""
        return True
    
    async def close(self):
        """Close connection (no-op for in-memory)."""
        pass
    
    def _cleanup_expired(self):
        """Remove expired keys."""
        now = datetime.now()
        expired_keys = [
            key for key, expiry in self._expiry.items()
            if expiry <= now
        ]
        for key in expired_keys:
            if key in self._store:
                del self._store[key]
            del self._expiry[key]