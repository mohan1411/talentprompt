"""Debug endpoints for troubleshooting."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api import deps
from app import crud, models
from app.core.config import settings

router = APIRouter()


@router.get("/debug/env")
async def check_environment():
    """Check critical environment variables."""
    return {
        "project_name": settings.PROJECT_NAME,
        "cors_origins": settings.BACKEND_CORS_ORIGINS,
        "database_url": "configured" if settings.DATABASE_URL else "missing",
        "secret_key": "configured" if settings.SECRET_KEY else "missing",
        "secret_key_length": len(settings.SECRET_KEY) if settings.SECRET_KEY else 0,
        "first_superuser": settings.FIRST_SUPERUSER,
        "api_version": settings.API_V1_STR,
    }


@router.get("/debug/database")
async def check_database(db: AsyncSession = Depends(deps.get_db)):
    """Check database connection and tables."""
    try:
        # Check connection
        result = await db.execute(text("SELECT 1"))
        connection_ok = result.scalar() == 1
        
        # Check if users table exists
        users_result = await db.execute(
            text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users'")
        )
        users_table_exists = users_result.scalar() > 0
        
        # Count users if table exists
        user_count = 0
        if users_table_exists:
            count_result = await db.execute(text("SELECT COUNT(*) FROM users"))
            user_count = count_result.scalar()
        
        return {
            "connection": "ok" if connection_ok else "failed",
            "users_table_exists": users_table_exists,
            "user_count": user_count,
        }
    except Exception as e:
        return {
            "connection": "failed",
            "error": str(e),
            "error_type": type(e).__name__,
        }


@router.get("/debug/auth-test")
async def test_auth_dependencies():
    """Test authentication dependencies."""
    try:
        from app.core.security import create_access_token
        from datetime import timedelta
        
        # Try creating a test token
        test_token = create_access_token(
            subject="test@example.com",
            expires_delta=timedelta(minutes=5)
        )
        
        return {
            "token_generation": "ok",
            "token_length": len(test_token),
            "password_context": "configured",
        }
    except Exception as e:
        return {
            "token_generation": "failed",
            "error": str(e),
            "error_type": type(e).__name__,
        }