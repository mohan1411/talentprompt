"""OAuth endpoints v2 - Proper OAuth flow for SPA."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from pydantic import BaseModel

from app.api import deps
from app.core.config import settings
from app.services.oauth import oauth_service
from app import crud
from app.core.security import create_access_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class OAuthTokenRequest(BaseModel):
    code: str
    provider: str
    redirect_uri: Optional[str] = None


class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


@router.post("/token", response_model=OAuthTokenResponse)
async def exchange_oauth_token(
    token_request: OAuthTokenRequest,
    db: AsyncSession = Depends(deps.get_db)
) -> OAuthTokenResponse:
    """Exchange OAuth authorization code for access token."""
    
    try:
        logger.info(f"OAuth token exchange request: provider={token_request.provider}, redirect_uri={token_request.redirect_uri}")
        
        # Get user info based on provider
        if token_request.provider == "google":
            oauth_data = await oauth_service.get_google_user_info(
                token_request.code, 
                token_request.redirect_uri
            )
        elif token_request.provider == "linkedin":
            oauth_data = await oauth_service.get_linkedin_user_info(
                token_request.code,
                token_request.redirect_uri  
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {token_request.provider}"
            )
        
        logger.info(f"OAuth data received for {oauth_data.get('email', 'unknown')}")
        
        # Check if user exists by OAuth provider
        user = await crud.user.get_by_oauth(
            db, 
            provider=token_request.provider, 
            provider_id=oauth_data["provider_id"]
        )
        
        if not user:
            # Check if user exists by email
            user = await crud.user.get_by_email(db, email=oauth_data["email"])
            
            if user:
                # Link OAuth account to existing user
                user = await crud.user.link_oauth_account(
                    db,
                    db_obj=user,
                    provider=token_request.provider,
                    provider_id=oauth_data["provider_id"],
                    oauth_data=oauth_data
                )
                logger.info(f"Linked {token_request.provider} account to existing user: {user.email}")
            else:
                # Create new OAuth user
                user = await crud.user.create_oauth_user(
                    db,
                    email=oauth_data["email"],
                    full_name=oauth_data.get("name", ""),
                    provider=token_request.provider,
                    provider_id=oauth_data["provider_id"],
                    oauth_data=oauth_data
                )
                logger.info(f"Created new user via {token_request.provider}: {user.email}")
        else:
            # Update OAuth data for existing user
            user = await crud.user.update_oauth_data(
                db, 
                db_obj=user, 
                oauth_data=oauth_data
            )
            logger.info(f"Updated OAuth data for existing user: {user.email}")
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )
        
        return OAuthTokenResponse(
            access_token=access_token,
            user={
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser
            }
        )
        
    except ValueError as e:
        logger.error(f"OAuth token exchange error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected OAuth error: {str(e)}", exc_info=True)
        # Return more detailed error in development
        if settings.DEBUG:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OAuth error: {str(e)}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete OAuth authentication"
        )