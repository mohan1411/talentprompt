"""Health check endpoints."""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.database import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, str]:
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
    }


@router.get("/db")
async def database_health(db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """Database connectivity check."""
    try:
        # Simple query to test database connection
        await db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/redis")
async def redis_health() -> Dict[str, str]:
    """Redis connectivity check."""
    # TODO: Implement Redis health check
    return {
        "status": "not_implemented",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/qdrant")
async def qdrant_health() -> Dict[str, any]:
    """Qdrant connectivity and configuration check."""
    import os
    
    qdrant_url = os.getenv("QDRANT_URL", settings.QDRANT_URL)
    has_api_key = bool(os.getenv("QDRANT_API_KEY", settings.QDRANT_API_KEY))
    
    # Mask sensitive parts of URL
    if qdrant_url and len(qdrant_url) > 20:
        masked_url = qdrant_url[:10] + "***" + qdrant_url[-10:]
    else:
        masked_url = qdrant_url
    
    result = {
        "status": "checking",
        "config": {
            "url": masked_url,
            "has_api_key": has_api_key,
            "collection_name": settings.QDRANT_COLLECTION_NAME,
            "is_localhost": "localhost" in qdrant_url or "127.0.0.1" in qdrant_url if qdrant_url else False
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    try:
        from app.services.vector_search import vector_search
        info = await vector_search.get_collection_info()
        result["status"] = "healthy" if info.get("status") == "connected" else "unhealthy"
        result["qdrant_info"] = info
    except Exception as e:
        result["status"] = "unhealthy"
        result["error"] = str(e)
        result["error_type"] = type(e).__name__
    
    return result