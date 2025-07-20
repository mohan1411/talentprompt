"""OAuth endpoints for social login."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.api import deps
from app.core.config import settings
from app.services.oauth import oauth_service
from app import crud
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import create_access_token
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Store OAuth states temporarily (in production, use Redis or database)
oauth_states: Dict[str, Dict[str, Any]] = {}


@router.get("/google/login")
async def google_login(
    redirect_uri: Optional[str] = Query(None, description="Frontend redirect URI after OAuth")
) -> Dict[str, str]:
    """Initiate Google OAuth flow."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured"
        )
    
    state = oauth_service.generate_state_token()
    oauth_states[state] = {
        "provider": "google",
        "redirect_uri": redirect_uri or f"{settings.FRONTEND_URL}/auth/google/callback"
    }
    
    auth_url = oauth_service.get_google_auth_url(state)
    
    return {
        "auth_url": auth_url,
        "state": state
    }


@router.get("/linkedin/login")
async def linkedin_login(
    redirect_uri: Optional[str] = Query(None, description="Frontend redirect URI after OAuth")
) -> Dict[str, str]:
    """Initiate LinkedIn OAuth flow."""
    if not settings.LINKEDIN_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="LinkedIn OAuth not configured"
        )
    
    state = oauth_service.generate_state_token()
    oauth_states[state] = {
        "provider": "linkedin",
        "redirect_uri": redirect_uri or f"{settings.FRONTEND_URL}/auth/linkedin/callback"
    }
    
    auth_url = oauth_service.get_linkedin_auth_url(state)
    
    return {
        "auth_url": auth_url,
        "state": state
    }


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State token for CSRF protection"),
    db: AsyncSession = Depends(deps.get_db)
) -> Dict[str, Any]:
    """Handle Google OAuth callback."""
    # Verify state
    if state not in oauth_states or oauth_states[state]["provider"] != "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    state_data = oauth_states.pop(state)
    
    try:
        # Get user info from Google
        logger.info(f"Exchanging Google code for user info. Code: {code[:10]}...")
        oauth_data = await oauth_service.get_google_user_info(code)
        logger.info(f"Got Google user info: {oauth_data.get('email', 'unknown')}")
        
        # Check if user exists by OAuth provider
        user = await crud.user.get_by_oauth(
            db, 
            provider="google", 
            provider_id=oauth_data.get("provider_id", oauth_data.get("google_id", oauth_data.get("id")))
        )
        
        if not user:
            # Check if user exists by email
            user = await crud.user.get_by_email(db, email=oauth_data["email"])
            
            if user:
                # Link OAuth account to existing user
                user = await crud.user.link_oauth_account(
                    db,
                    db_obj=user,
                    provider="google",
                    provider_id=oauth_data.get("provider_id", oauth_data.get("google_id", oauth_data.get("id"))),
                    oauth_data=oauth_data
                )
            else:
                # Create new OAuth user
                user = await crud.user.create_oauth_user(
                    db,
                    email=oauth_data["email"],
                    full_name=oauth_data.get("name", ""),
                    provider="google",
                    provider_id=oauth_data.get("provider_id", oauth_data.get("google_id", oauth_data.get("id"))),
                    oauth_data=oauth_data
                )
        else:
            # Update OAuth data for existing user
            user = await crud.user.update_oauth_data(
                db, 
                db_obj=user, 
                oauth_data=oauth_data
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )
        
        # Redirect to frontend with token
        redirect_url = f"{state_data['redirect_uri']}?token={access_token}&provider=google"
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "redirect_url": redirect_url,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name
            }
        }
        
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}")
        error_redirect = f"{state_data['redirect_uri']}?error=oauth_failed&provider=google"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}"
        )


@router.get("/linkedin/callback")
async def linkedin_callback(
    code: str = Query(..., description="Authorization code from LinkedIn"),
    state: str = Query(..., description="State token for CSRF protection"),
    db: AsyncSession = Depends(deps.get_db)
) -> Dict[str, Any]:
    """Handle LinkedIn OAuth callback."""
    # Verify state
    if state not in oauth_states or oauth_states[state]["provider"] != "linkedin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    state_data = oauth_states.pop(state)
    
    try:
        # Get user info from LinkedIn
        oauth_data = await oauth_service.get_linkedin_user_info(code)
        
        # Check if user exists by OAuth provider
        user = await crud.user.get_by_oauth(
            db, 
            provider="linkedin", 
            provider_id=oauth_data.get("provider_id", oauth_data.get("google_id", oauth_data.get("id")))
        )
        
        if not user:
            # Check if user exists by email
            user = await crud.user.get_by_email(db, email=oauth_data["email"])
            
            if user:
                # Link OAuth account to existing user
                user = await crud.user.link_oauth_account(
                    db,
                    db_obj=user,
                    provider="linkedin",
                    provider_id=oauth_data.get("provider_id", oauth_data.get("google_id", oauth_data.get("id"))),
                    oauth_data=oauth_data
                )
            else:
                # Create new OAuth user
                user = await crud.user.create_oauth_user(
                    db,
                    email=oauth_data["email"],
                    full_name=oauth_data.get("name", ""),
                    provider="linkedin",
                    provider_id=oauth_data.get("provider_id", oauth_data.get("google_id", oauth_data.get("id"))),
                    oauth_data=oauth_data
                )
        else:
            # Update OAuth data for existing user
            user = await crud.user.update_oauth_data(
                db, 
                db_obj=user, 
                oauth_data=oauth_data
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )
        
        # Redirect to frontend with token
        redirect_url = f"{state_data['redirect_uri']}?token={access_token}&provider=linkedin"
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "redirect_url": redirect_url,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name
            }
        }
        
    except Exception as e:
        logger.error(f"LinkedIn OAuth error: {str(e)}")
        error_redirect = f"{state_data['redirect_uri']}?error=oauth_failed&provider=linkedin"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}"
        )


@router.post("/link/{provider}")
async def link_oauth_account(
    provider: str,
    oauth_data: Dict[str, Any],
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Dict[str, str]:
    """Link an OAuth account to existing user."""
    if provider not in ["google", "linkedin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth provider"
        )
    
    # Link OAuth account to current user
    await crud.user.link_oauth_account(
        db,
        db_obj=current_user,
        provider=provider,
        provider_id=oauth_data.get("provider_id"),
        oauth_data=oauth_data
    )
    
    return {"message": f"{provider.title()} account linked successfully"}