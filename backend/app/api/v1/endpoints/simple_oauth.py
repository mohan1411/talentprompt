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
async def google_oauth_login(redirect_uri: Optional[str] = None):
    """Initiate Google OAuth login flow."""
    # Generate a random state for CSRF protection
    state = secrets.token_urlsafe(32)
    
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
        "redirect_uri": f"{settings.API_URL}/api/v1/oauth/google/callback",
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
    # Verify state
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    state_data = oauth_states.pop(state)
    redirect_uri = state_data["redirect_uri"]
    
    # In a real implementation, you would exchange the code for tokens
    # For now, we'll simulate this with a mock implementation
    
    # Mock user data (in production, get this from Google)
    mock_user_data = {
        "email": "promtitude@gmail.com",  # Default test user
        "name": "Test User",
        "google_id": "mock_google_id_123"
    }
    
    # Check if user exists
    user = await get_user_by_email(db, email=mock_user_data["email"])
    
    if not user:
        # For this simple implementation, we won't create new users
        # Just return an error
        error_params = urlencode({"error": "user_not_found", "message": "User not found. Please register first."})
        return RedirectResponse(url=f"{redirect_uri}?{error_params}")
    
    # Verify user is an OAuth user
    if not user.oauth_provider:
        error_params = urlencode({"error": "not_oauth_user", "message": "This account uses password authentication."})
        return RedirectResponse(url=f"{redirect_uri}?{error_params}")
    
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