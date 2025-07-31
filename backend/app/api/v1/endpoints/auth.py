"""Authentication endpoints."""

import logging
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.database import get_db
from app.api import deps
from app.core.config import settings
from app.core.security import create_access_token
from app.crud.user import authenticate_user, create_user, get_user_by_email
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import User as UserSchema, UserCreate
from app.services.recaptcha import recaptcha_service
from app.services.email_verification import email_verification_service
from app.services.email import email_service
from app.services.extension_token import extension_token_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Simple OAuth endpoint for frontend compatibility
@router.get("/oauth/google/login")
async def google_oauth_login():
    """Simple OAuth endpoint that works without authlib for development."""
    # For development, redirect to a mock OAuth flow
    mock_oauth_url = "http://localhost:8001/api/v1/auth/oauth/mock/select-user"
    return {
        "auth_url": mock_oauth_url,
        "state": "dummy_state"
    }

@router.get("/oauth/mock/select-user")
async def mock_oauth_select_user():
    """Mock OAuth user selection page for development."""
    html = """
    <html>
    <head>
        <title>Select OAuth User - Development</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .user-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; cursor: pointer; }
            .user-card:hover { background-color: #f5f5f5; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <h1>Select OAuth User (Development Mode)</h1>
        <p>Click on a user to login:</p>
        
        <div class="user-card" onclick="selectUser('promtitude@gmail.com')">
            <strong>promtitude@gmail.com</strong><br>
            Provider: Google
        </div>
        
        <div class="user-card" onclick="selectUser('taskmasterai1411@gmail.com')">
            <strong>taskmasterai1411@gmail.com</strong><br>
            Provider: Google
        </div>
        
        <div class="user-card" onclick="selectUser('mohan.g1411@gmail.com')">
            <strong>mohan.g1411@gmail.com</strong><br>
            Provider: Google
        </div>
        
        <script>
            function selectUser(email) {
                window.location.href = '/api/v1/auth/oauth/mock/callback?email=' + encodeURIComponent(email);
            }
        </script>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)

@router.get("/oauth/mock/callback")
async def mock_oauth_callback(email: str, db: AsyncSession = Depends(get_db)):
    """Mock OAuth callback that authenticates existing OAuth users."""
    # Find the user
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.oauth_provider:
        raise HTTPException(status_code=400, detail="User is not an OAuth user")
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    # Redirect to frontend with token
    redirect_url = f"http://localhost:3000/auth/callback?access_token={access_token}&token_type=bearer&email={email}"
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=redirect_url)


@router.post("/register", response_model=UserSchema)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Register new user."""
    # Verify reCAPTCHA token
    if user_in.recaptcha_token:
        is_valid = await recaptcha_service.verify_token(
            token=user_in.recaptcha_token,
            action="register"
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="reCAPTCHA verification failed. Please try again."
            )
    
    # Check if user already exists
    user = await get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    user = await create_user(db, user_create=user_in)
    
    # Generate verification token and send email
    verification_token = await email_verification_service.create_verification_token(
        db=db,
        user_id=str(user.id)
    )
    
    # Build verification URL
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    
    # Send verification email
    await email_service.send_verification_email(
        to_email=user.email,
        full_name=user.full_name or user.username,
        verification_url=verification_url
    )
    
    # TODO: Store marketing_opt_in preference in user preferences table
    
    return user


@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login."""
    logger.info(f"Login attempt for: {form_data.username}")
    
    # First try standard password authentication
    user = await authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        # Check if this is an OAuth user trying to use an access token
        user = await get_user_by_email(db, email=form_data.username)
        logger.info(f"User found: {user is not None}, OAuth provider: {user.oauth_provider if user else None}")
        
        if user and user.oauth_provider:
            # This is an OAuth user - check if password is actually an access token
            logger.info(f"OAuth user {form_data.username} attempting token login")
            # First check token validity WITHOUT consuming it
            token_valid = await extension_token_service.verify_token(form_data.username, form_data.password, consume=False)
            logger.info(f"Token verification result: {token_valid}")
            
            if token_valid:
                # Valid access token - proceed with login checks
                logger.info(f"Valid access token for {form_data.username}, checking other requirements")
                # Token will be consumed later after all checks pass
            else:
                # OAuth user needs to get an access token
                logger.info(f"OAuth user {form_data.username} needs access token")
                
                # Always provide the URL for OAuth users
                auth_url = f"{settings.FRONTEND_URL}/extension-auth?email={form_data.username}"
                
                # Check if they tried to enter an access code
                if form_data.password and len(form_data.password) == settings.EXTENSION_TOKEN_LENGTH:
                    # They tried an access code but it was invalid
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Invalid access code. Get a new one at: {auth_url}",
                        headers={"WWW-Authenticate": "Bearer"}
                    )
                else:
                    # They didn't enter an access code or entered something else
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"OAuth users need an access code. Get yours at: {auth_url}",
                        headers={"WWW-Authenticate": "Bearer"}
                    )
        else:
            # Regular user with wrong password
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Check if user's email is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in. Check your inbox for the verification link.",
        )
    
    # If this was an OAuth user with a valid token, we already verified it above
    # We don't consume it to allow multiple logins within the expiration window
    if user.oauth_provider and form_data.password and len(form_data.password) == settings.EXTENSION_TOKEN_LENGTH:
        logger.info(f"OAuth user {form_data.username} logged in with extension token (not consumed)")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout() -> Any:
    """Logout user."""
    # For JWT, logout is typically handled client-side by removing the token
    # Here we can add token blacklisting if needed
    return {"msg": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token() -> Any:
    """Refresh access token."""
    # TODO: Implement refresh token logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not yet implemented",
    )


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Verify user's email address."""
    user = await email_verification_service.verify_token(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Send welcome email
    await email_service.send_welcome_email(
        to_email=user.email,
        full_name=user.full_name or user.username
    )
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(
    email: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Resend verification email."""
    # Get user by email
    user = await get_user_by_email(db, email=email)
    
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a verification email has been sent"}
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Resend verification email
    success = await email_verification_service.resend_verification_email(db, user)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    return {"message": "Verification email has been sent"}


@router.post("/generate-extension-token")
async def generate_extension_token(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Generate an access token for Chrome extension (OAuth users only)."""
    # Check if user is OAuth user
    if not current_user.oauth_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access tokens are only for OAuth users. Please use your password to login."
        )
    
    # Generate token
    token = await extension_token_service.generate_token(current_user.email)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many token requests. Please try again later."
        )
    
    return {
        "access_token": token,
        "expires_in": settings.EXTENSION_TOKEN_EXPIRE_SECONDS,
        "message": "Use this code in the Chrome extension password field"
    }


@router.get("/extension-token-status")
async def get_extension_token_status(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Check if user has an active extension token."""
    status = await extension_token_service.get_token_status(current_user.email)
    
    return {
        "has_token": status["has_token"],
        "ttl": status["ttl"],
        "is_oauth_user": bool(current_user.oauth_provider)
    }


@router.delete("/revoke-extension-token")
async def revoke_extension_token(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Revoke any existing extension token."""
    revoked = await extension_token_service.revoke_token(current_user.email)
    
    if revoked:
        return {"message": "Extension token revoked successfully"}
    else:
        return {"message": "No active token to revoke"}


@router.post("/check-oauth-user")
async def check_oauth_user(
    email: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Check if an email belongs to an OAuth user."""
    user = await get_user_by_email(db, email=email)
    
    if not user:
        return {"is_oauth_user": False, "exists": False}
    
    return {
        "is_oauth_user": bool(user.oauth_provider),
        "exists": True,
        "oauth_provider": user.oauth_provider
    }