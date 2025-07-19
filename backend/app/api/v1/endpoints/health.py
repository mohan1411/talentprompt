"""Health check endpoints."""

from datetime import datetime
from typing import Dict, Any

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
async def qdrant_health() -> Dict[str, str]:
    """Qdrant connectivity check - simplified to avoid type issues."""
    try:
        import os
        qdrant_url = os.getenv("QDRANT_URL", settings.QDRANT_URL)
        
        # Basic check
        if "localhost" in qdrant_url:
            return {
                "status": "warning",
                "message": "Qdrant configured for localhost",
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        # Try to check collection
        try:
            from app.services.vector_search import vector_search
            info = await vector_search.get_collection_info()
            return {
                "status": "healthy",
                "message": f"Connected to Qdrant with {info.get('points_count', 0)} vectors",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Qdrant error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Configuration error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }