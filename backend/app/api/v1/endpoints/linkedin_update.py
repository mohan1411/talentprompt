"""LinkedIn profile update endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from app.api import deps
from app.models.user import User
from app.models.resume import Resume

logger = logging.getLogger(__name__)

router = APIRouter()


class UpdateContactInfo(BaseModel):
    """Update contact information request."""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


@router.patch("/{resume_id}/contact", response_model=dict)
async def update_contact_info(
    resume_id: UUID,
    contact_info: UpdateContactInfo,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> dict:
    """Update contact information for a LinkedIn-imported resume."""
    
    # Get the resume
    query = select(Resume).where(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    )
    result = await db.execute(query)
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Update contact info
    if contact_info.email is not None:
        resume.email = contact_info.email
    if contact_info.phone is not None:
        resume.phone = contact_info.phone
    
    await db.commit()
    await db.refresh(resume)
    
    return {
        "success": True,
        "message": "Contact information updated",
        "email": resume.email,
        "phone": resume.phone
    }