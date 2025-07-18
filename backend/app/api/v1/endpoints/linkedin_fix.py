"""LinkedIn import fix endpoints."""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_

from app.api import deps
from app.models.user import User
from app.models.resume import Resume
from app.api.v1.endpoints.linkedin import LinkedInProfileImport, LinkedInImportResponse
from app.services.linkedin_parser import LinkedInParser
from app.services.vector_search import vector_search
from app.services.search_skill_fix import normalize_skill_for_storage

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/import-or-update", response_model=LinkedInImportResponse)
async def import_or_update_linkedin_profile(
    profile_data: LinkedInProfileImport,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> LinkedInImportResponse:
    """Import or update a LinkedIn profile, handling duplicates gracefully."""
    
    # Normalize LinkedIn URL
    normalized_url = profile_data.linkedin_url.split('?')[0].rstrip('/')
    
    logger.info(f"Import or update profile: {normalized_url}")
    
    # Try to find existing profile with various URL formats
    existing_resume = None
    
    # Check exact match
    result = await db.execute(
        select(Resume).where(
            Resume.linkedin_url == normalized_url,
            Resume.user_id == current_user.id,
            Resume.status != 'deleted'
        )
    )
    existing_resume = result.scalar_one_or_none()
    
    # Check with trailing slash
    if not existing_resume:
        result = await db.execute(
            select(Resume).where(
                Resume.linkedin_url == normalized_url + '/',
                Resume.user_id == current_user.id,
                Resume.status != 'deleted'
            )
        )
        existing_resume = result.scalar_one_or_none()
    
    # Check if URL contains the normalized URL (handles cases with query params in DB)
    if not existing_resume:
        result = await db.execute(
            select(Resume).where(
                Resume.linkedin_url.contains(normalized_url),
                Resume.user_id == current_user.id,
                Resume.status != 'deleted'
            )
        )
        existing_resume = result.scalar_one_or_none()
    
    try:
        # Parse LinkedIn data
        parser = LinkedInParser()
        parsed_data = await parser.parse_linkedin_data(profile_data.dict())
        
        if existing_resume:
            # Update existing resume
            logger.info(f"Updating existing resume ID: {existing_resume.id}")
            
            # Update fields
            existing_resume.first_name = parsed_data.get("first_name", existing_resume.first_name)
            existing_resume.last_name = parsed_data.get("last_name", existing_resume.last_name)
            existing_resume.location = profile_data.location or existing_resume.location
            existing_resume.summary = profile_data.about or existing_resume.summary
            existing_resume.current_title = profile_data.headline or existing_resume.current_title
            existing_resume.years_experience = profile_data.years_experience or existing_resume.years_experience
            existing_resume.last_linkedin_sync = datetime.utcnow()
            existing_resume.linkedin_data = profile_data.dict()
            existing_resume.parsed_data = parsed_data
            existing_resume.raw_text = parsed_data.get("raw_text", "")
            
            # Update skills if provided
            if profile_data.skills:
                normalized_skills = [normalize_skill_for_storage(skill) for skill in profile_data.skills]
                existing_resume.skills = normalized_skills
                logger.info(f"Updated skills: {normalized_skills}")
            
            # Update keywords
            if parsed_data.get("keywords"):
                existing_resume.keywords = parsed_data.get("keywords", [])
            
            await db.commit()
            await db.refresh(existing_resume)
            
            # Re-index in vector search - temporarily disabled due to greenlet issue
            # TODO: Fix async context issue with reindex_service
            # try:
            #     from app.services.reindex_service import reindex_service
            #     await reindex_service.reindex_resume(db, existing_resume)
            # except Exception as e:
            #     logger.error(f"Failed to reindex resume: {e}")
            
            return LinkedInImportResponse(
                success=True,
                candidate_id=existing_resume.id,
                message=f"Profile updated successfully. Skills: {len(existing_resume.skills or [])}, Years: {existing_resume.years_experience}",
                is_duplicate=True
            )
        else:
            # Create new resume
            logger.info("Creating new resume")
            
            resume_data = {
                "user_id": current_user.id,
                "first_name": parsed_data.get("first_name", ""),
                "last_name": parsed_data.get("last_name", ""),
                "email": profile_data.email or parsed_data.get("email", ""),
                "phone": profile_data.phone or parsed_data.get("phone", ""),
                "location": profile_data.location or "",
                "summary": profile_data.about or "",
                "current_title": profile_data.headline or "",
                "years_experience": profile_data.years_experience or parsed_data.get("years_experience", 0),
                "skills": [normalize_skill_for_storage(skill) for skill in (profile_data.skills or [])],
                "keywords": parsed_data.get("keywords", []),
                "linkedin_url": normalized_url,
                "linkedin_data": profile_data.dict(),
                "last_linkedin_sync": datetime.utcnow(),
                "status": "active",
                "parse_status": "completed",
                "parsed_at": datetime.utcnow(),
                "raw_text": parsed_data.get("raw_text", ""),
                "parsed_data": parsed_data
            }
            
            logger.info(f"Creating resume with skills: {resume_data['skills']}")
            
            resume = Resume(**resume_data)
            db.add(resume)
            await db.flush()
            
            # Generate embedding for vector search
            if profile_data.about or profile_data.headline:
                search_text = f"{profile_data.headline or ''} {profile_data.about or ''}"
                embedding = await vector_search.index_resume(
                    resume_id=str(resume.id),
                    text=search_text,
                    metadata={
                        "name": f"{parsed_data.get('first_name', '')} {parsed_data.get('last_name', '')}",
                        "skills": resume_data['skills'],
                        "location": resume_data['location'],
                        "years_experience": resume_data['years_experience']
                    }
                )
            
            await db.commit()
            
            return LinkedInImportResponse(
                success=True,
                candidate_id=resume.id,
                message=f"Profile imported successfully. Skills: {len(resume_data['skills'])}, Years: {resume_data['years_experience']}",
                is_duplicate=False
            )
            
    except Exception as e:
        logger.error(f"Failed to import/update profile: {str(e)}")
        await db.rollback()
        
        # If it's a unique constraint error, try to find and update the existing profile
        if "duplicate key value violates unique constraint" in str(e):
            # Find the existing profile by URL
            result = await db.execute(
                select(Resume).where(
                    Resume.linkedin_url == normalized_url,
                    Resume.user_id == current_user.id
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                return LinkedInImportResponse(
                    success=False,
                    candidate_id=existing.id,
                    message="Profile already exists. Please refresh and try again.",
                    is_duplicate=True
                )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import profile: {str(e)}"
        )