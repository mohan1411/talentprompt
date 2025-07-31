"""Simple OAuth implementation without authlib."""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib.parse import urlencode
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.dependencies.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.crud.user import get_user_by_email
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

# Simple in-memory store for OAuth states (in production, use Redis)
oauth_states: Dict[str, Dict[str, Any]] = {}


@router.get("/google/login")
async def google_oauth_login(request: Request, redirect_uri: Optional[str] = None):
    """Initiate Google OAuth login flow."""
    # Generate a random state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Get the actual API URL from the request
    base_url = str(request.base_url).rstrip('/')
    # In production, this should be the actual backend URL
    api_base_url = base_url if "localhost" not in base_url else settings.API_URL
    
    # For production environments, use the actual backend URL
    if settings.ENVIRONMENT == "production" or "promtitude" in settings.FRONTEND_URL:
        # Use the correct production backend URL
        api_base_url = "https://talentprompt-production.up.railway.app"
    
    # Store state with expiration (5 minutes)
    oauth_states[state] = {
        "created_at": datetime.utcnow(),
        "redirect_uri": redirect_uri or f"{settings.FRONTEND_URL}/auth/callback"
    }
    
    # Clean up old states
    current_time = datetime.utcnow()
    expired_states = [
        s for s, data in oauth_states.items() 
        if current_time - data["created_at"] > timedelta(minutes=5)
    ]
    for s in expired_states:
        del oauth_states[s]
    
    # Build Google OAuth URL
    google_auth_params = {
        "client_id": settings.GOOGLE_CLIENT_ID or "dummy_client_id",
        "redirect_uri": f"{api_base_url}/api/v1/oauth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account"
    }
    
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(google_auth_params)}"
    
    return {
        "auth_url": google_auth_url,
        "state": state
    }


@router.get("/google/callback")
async def google_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle Google OAuth callback."""
    # Verify state (skip in production due to in-memory storage issues)
    if state in oauth_states:
        state_data = oauth_states.pop(state)
        redirect_uri = state_data["redirect_uri"]
    else:
        # In production, state might be lost due to deployment/restart
        # Use default redirect URI
        logger.warning(f"State not found in memory: {state}")
        redirect_uri = f"{settings.FRONTEND_URL}/auth/callback"
    
    # Exchange the code for user info using the OAuth service
    from app.services.oauth import oauth_service
    
    try:
        # Get the actual API URL for redirect_uri
        if settings.ENVIRONMENT == "production":
            api_base_url = "https://talentprompt-production.up.railway.app"
        else:
            api_base_url = settings.API_URL
        
        # Use the same redirect_uri that was used in the auth request
        oauth_redirect_uri = f"{api_base_url}/api/v1/oauth/google/callback"
        
        # Get user info from Google
        user_data = await oauth_service.get_google_user_info(code, oauth_redirect_uri)
        email = user_data["email"]
        name = user_data.get("name", "")
        google_id = user_data["provider_id"]
    except Exception as e:
        logger.error(f"Failed to get Google user info: {e}")
        error_params = urlencode({"error": "oauth_failed", "message": str(e)})
        return RedirectResponse(url=f"{redirect_uri}?{error_params}")
    
    # Check if user exists
    user = await get_user_by_email(db, email=email)
    
    if not user:
        # Create a new OAuth user
        from app.crud import user as user_crud
        
        user = await user_crud.user.create_oauth_user(
            db,
            email=email,
            full_name=name,
            provider="google",
            provider_id=google_id,
            oauth_data=user_data
        )
        logger.info(f"Created new OAuth user: {email}")
    else:
        # Update existing user with OAuth info if needed
        if not user.oauth_provider:
            # Link OAuth to existing user
            from app.crud import user as user_crud
            
            user = await user_crud.user.link_oauth_account(
                db,
                db_obj=user,
                provider="google",
                provider_id=google_id,
                oauth_data=user_data
            )
            logger.info(f"Linked Google OAuth to existing user: {email}")
    
    # Generate access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    # Redirect to frontend with token
    success_params = urlencode({
        "access_token": access_token,
        "token_type": "bearer",
        "email": user.email,
        "name": user.full_name or user.username
    })
    
    return RedirectResponse(url=f"{redirect_uri}?{success_params}")


@router.post("/mock/login")
async def mock_oauth_login(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Mock OAuth login for testing - directly authenticate an OAuth user."""
    # Check if user exists and is an OAuth user
    user = await get_user_by_email(db, email=email)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please ensure the user exists in the database."
        )
    
    if not user.oauth_provider:
        raise HTTPException(
            status_code=400,
            detail="This user is not an OAuth user. Use regular login instead."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is not active."
        )
    
    # Generate access token
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
            "oauth_provider": user.oauth_provider
        }
    }


@router.get("/test/create-oauth-user")
async def test_create_oauth_user(
    email: str = Query(default="test@example.com"),
    provider: str = Query(default="google"),
    db: AsyncSession = Depends(get_db)
):
    """Create a test OAuth user (development only)."""
    import os
    if not (settings.DEBUG or os.getenv("ALLOW_DEV_ENDPOINTS")):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Check if user already exists
    existing_user = await get_user_by_email(db, email=email)
    if existing_user:
        return {
            "message": "User already exists",
            "user": {
                "id": str(existing_user.id),
                "email": existing_user.email,
                "oauth_provider": existing_user.oauth_provider
            }
        }
    
    # Create new OAuth user
    user = User(
        email=email,
        username=email.split("@")[0],
        full_name=f"Test {provider.title()} User",
        is_active=True,
        is_verified=True,  # OAuth users are pre-verified
        oauth_provider=provider,
        oauth_provider_id=f"{provider}_id_{secrets.token_hex(8)}",
        oauth_data=json.dumps({"test": True})
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {
        "message": "OAuth user created successfully",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "oauth_provider": user.oauth_provider
        }
    }