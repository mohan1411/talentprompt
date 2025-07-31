"""OAuth endpoints for frontend callback flow."""

import logging
from typing import Optional
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.v1.dependencies.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.services.oauth import oauth_service
from app.crud import user as user_crud

router = APIRouter()
logger = logging.getLogger(__name__)


class OAuthCodeExchange(BaseModel):
    """Request model for OAuth code exchange."""
    code: str
    state: str
    provider: str = "google"


@router.post("/exchange-code")
async def exchange_oauth_code(
    request: OAuthCodeExchange,
    db: AsyncSession = Depends(get_db)
):
    """Exchange OAuth authorization code for access token."""
    try:
        # Get user info from OAuth provider
        if request.provider == "google":
            # Use frontend callback URL since that's what Google has authorized
            redirect_uri = f"{settings.FRONTEND_URL}/auth/google/callback"
            user_data = await oauth_service.get_google_user_info(request.code, redirect_uri)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")
        
        email = user_data["email"]
        name = user_data.get("name", "")
        provider_id = user_data["provider_id"]
        
        # Check if user exists
        user = await user_crud.user.get_by_email(db, email=email)
        
        if not user:
            # Create new OAuth user
            user = await user_crud.user.create_oauth_user(
                db,
                email=email,
                full_name=name,
                provider=request.provider,
                provider_id=provider_id,
                oauth_data=user_data
            )
            logger.info(f"Created new OAuth user: {email}")
        else:
            # Update existing user with OAuth info if needed
            if not user.oauth_provider:
                user = await user_crud.user.link_oauth_account(
                    db,
                    db_obj=user,
                    provider=request.provider,
                    provider_id=provider_id,
                    oauth_data=user_data
                )
                logger.info(f"Linked {request.provider} OAuth to existing user: {email}")
        
        # Generate JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "username": user.username,
                "is_verified": user.is_verified
            }
        }
        
    except Exception as e:
        logger.error(f"OAuth code exchange failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))