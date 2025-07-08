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