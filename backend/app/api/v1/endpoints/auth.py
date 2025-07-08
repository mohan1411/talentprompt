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

router = APIRouter()


@router.post("/register", response_model=User)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Register new user."""
    # Check if user already exists
    user = await get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    user = await create_user(db, user_create=user_in)
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