"""LinkedIn integration endpoints - Version without LinkedIn columns."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
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
        # Parse LinkedIn data first
        parser = LinkedInParser()
        parsed_data = await parser.parse_linkedin_data(profile_data.dict())
        
        # Check if a profile with same name already exists (workaround for missing linkedin_url column)
        first_name = parsed_data.get("first_name", "")
        last_name = parsed_data.get("last_name", "")
        
        if first_name and last_name:
            existing_query = select(Resume).where(
                and_(
                    Resume.user_id == current_user.id,
                    Resume.first_name == first_name,
                    Resume.last_name == last_name
                )
            )
            existing_result = await db.execute(existing_query)
            existing_resume = existing_result.scalar_one_or_none()
            
            if existing_resume:
                return LinkedInImportResponse(
                    success=True,
                    candidate_id=existing_resume.id,
                    message=f"Profile for {first_name} {last_name} already exists",
                    is_duplicate=True
                )
        
        # Create new resume without LinkedIn-specific columns
        resume_data = {
            "user_id": current_user.id,
            "first_name": first_name or "Unknown",
            "last_name": last_name or "Name",
            "email": parsed_data.get("email", ""),
            "phone": parsed_data.get("phone", ""),
            "location": profile_data.location or "",
            "summary": profile_data.about or "",
            "current_title": profile_data.headline or "",
            "years_experience": parsed_data.get("years_experience", 0),
            "skills": profile_data.skills or [],
            "keywords": parsed_data.get("keywords", []),
            "status": "active",
            "parse_status": "completed",
            "parsed_at": datetime.utcnow(),
            "raw_text": parsed_data.get("raw_text", ""),
            "parsed_data": {
                **parsed_data,
                "linkedin_url": profile_data.linkedin_url,  # Store in parsed_data JSON
                "linkedin_data": profile_data.dict(),
                "imported_from": "linkedin",
                "import_date": datetime.utcnow().isoformat()
            }
        }
        
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
        logger.exception(e)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import profile: {str(e)}"
        )