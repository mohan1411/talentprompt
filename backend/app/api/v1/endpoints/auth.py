"""Authentication endpoints."""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.crud.user import authenticate_user, create_user, get_user_by_email
from app.schemas.token import Token
from app.schemas.user import User, UserCreate
from app.services.recaptcha import recaptcha_service
from app.services.email_verification import email_verification_service
from app.services.email import email_service

router = APIRouter()


@router.post("/register", response_model=User)
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
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
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