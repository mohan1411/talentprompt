"""User management endpoints."""

from typing import Any, List

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/")
async def get_users() -> List[Any]:
    """Get all users."""
    # TODO: Implement user retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User retrieval not yet implemented",
    )


@router.get("/me")
async def get_current_user() -> Any:
    """Get current user."""
    # TODO: Implement current user retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Current user retrieval not yet implemented",
    )


@router.post("/")
async def create_user() -> Any:
    """Create new user."""
    # TODO: Implement user creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User creation not yet implemented",
    )