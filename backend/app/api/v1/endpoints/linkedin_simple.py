"""LinkedIn integration endpoints - Simplified version without vector search."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.api import deps
from app.models.user import User
from app.models.resume import Resume
from app.crud import resume as crud_resume
from app.services.linkedin_parser import LinkedInParser

logger = logging.getLogger(__name__)

router = APIRouter()


class LinkedInProfileImport(BaseModel):
    """LinkedIn profile import request."""
    linkedin_url: str = Field(..., description="LinkedIn profile URL")
    name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    about: Optional[str] = None
    experience: Optional[list] = []
    education: Optional[list] = []
    skills: Optional[list] = []
    full_text: Optional[str] = None  # Full resume text
    years_experience: Optional[int] = None  # Total years of experience


class LinkedInImportResponse(BaseModel):
    """LinkedIn import response."""
    success: bool
    candidate_id: Optional[UUID] = None
    message: str
    is_duplicate: bool = False


@router.post("/import-profile", response_model=LinkedInImportResponse)
async def import_linkedin_profile(
    profile_data: LinkedInProfileImport,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> LinkedInImportResponse:
    """Import a LinkedIn profile to the database."""
    
    try:
        # Check if profile already exists
        existing_query = select(Resume).where(Resume.linkedin_url == profile_data.linkedin_url)
        existing_result = await db.execute(existing_query)
        existing_resume = existing_result.scalar_one_or_none()
        
        if existing_resume:
            # Update last sync time
            existing_resume.last_linkedin_sync = datetime.utcnow()
            await db.commit()
            
            return LinkedInImportResponse(
                success=True,
                candidate_id=existing_resume.id,
                message="Profile already exists in database",
                is_duplicate=True
            )
        
        # Parse LinkedIn data (will use AI if available and full_text is provided)
        parser = LinkedInParser()
        parsed_data = await parser.parse_linkedin_data(profile_data.dict())
        
        # Create new resume
        # Use AI-parsed data when available, fallback to raw data
        resume_data = {
            "user_id": current_user.id,
            "first_name": parsed_data.get("first_name", ""),
            "last_name": parsed_data.get("last_name", ""),
            "email": parsed_data.get("email", ""),
            "phone": parsed_data.get("phone", ""),
            "location": parsed_data.get("location") or profile_data.location or "",
            "summary": parsed_data.get("summary") or profile_data.about or "",
            "current_title": parsed_data.get("current_title") or profile_data.headline or "",
            "years_experience": parsed_data.get("years_experience") or profile_data.years_experience or 0,
            "skills": parsed_data.get("skills") or profile_data.skills or [],
            "keywords": parsed_data.get("keywords", []),
            "linkedin_url": profile_data.linkedin_url,
            "linkedin_data": profile_data.dict(),
            "last_linkedin_sync": datetime.utcnow(),
            "status": "active",
            "parse_status": "completed",
            "parsed_at": datetime.utcnow(),
            "raw_text": parsed_data.get("raw_text", ""),
            "parsed_data": parsed_data
        }
        
        # Log parsing method for debugging
        parsing_method = parsed_data.get("parsing_method", "rule-based")
        logger.info(f"Resume created using {parsing_method} parsing")
        
        resume = Resume(**resume_data)
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        
        logger.info(f"Successfully imported LinkedIn profile: {profile_data.linkedin_url}")
        
        return LinkedInImportResponse(
            success=True,
            candidate_id=resume.id,
            message="Profile imported successfully",
            is_duplicate=False
        )
        
    except Exception as e:
        logger.error(f"Failed to import LinkedIn profile: {str(e)}")
        logger.exception(e)  # This will log the full traceback
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import profile: {str(e)}"
        )