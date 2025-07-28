"""Temporary dev endpoint for OAuth token generation."""

from fastapi import APIRouter, Depends, HTTPException
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from jose import jwt
from uuid import uuid4
import os

from app.core.config import settings
from app.api.deps import get_db
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/dev/generate-oauth-token")
async def generate_oauth_token(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate token for OAuth user (DEV ONLY - REMOVE IN PRODUCTION)."""
    
    logger.info(f"Dev token generation requested for email: {email}")
    logger.info(f"DEBUG setting: {settings.DEBUG}")
    
    # Check if this is development environment
    # Allow if DEBUG is True OR if ALLOW_DEV_ENDPOINTS is set
    if not (settings.DEBUG or os.getenv("ALLOW_DEV_ENDPOINTS")):
        logger.warning("Dev endpoint blocked - not in development mode")
        raise HTTPException(status_code=404, detail="Not found")
    
    # Get user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User {email} not found")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is not active")
    
    # Create access token
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user.id),  # Use user ID, not email, to match production behavior
        "user_id": str(user.id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid4())
    }
    
    access_token = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active
        },
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
    }