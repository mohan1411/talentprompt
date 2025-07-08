"""User management endpoints."""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.dependencies.auth import get_current_active_user, get_current_superuser
from app.api.v1.dependencies.database import get_db
from app.crud.user import get_user, update_user
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[UserSchema])
async def get_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
) -> Any:
    """Get all users (superuser only)."""
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return users


@router.get("/me", response_model=UserSchema)
async def get_current_user(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get current user."""
    return current_user


@router.put("/me", response_model=UserSchema)
async def update_current_user(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update current user."""
    user = await update_user(db, db_user=current_user, user_update=user_update)
    return user


@router.get("/{user_id}", response_model=UserSchema)
async def get_user_by_id(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get user by ID."""
    user = await get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Users can only view their own profile unless they're superuser
    if user.id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return user