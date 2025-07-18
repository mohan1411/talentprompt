"""LinkedIn integration endpoints."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel, Field, HttpUrl

from app.api import deps
from app.models.user import User
from app.models.resume import Resume
from app.crud import resume as crud_resume
from app.services.linkedin_parser import LinkedInParser
from app.services.vector_search import vector_search
from app.services.search_skill_fix import normalize_skill_for_storage

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
    email: Optional[str] = None
    phone: Optional[str] = None
    years_experience: Optional[int] = None


class LinkedInCheckExistsRequest(BaseModel):
    """Check if LinkedIn profile exists request."""
    linkedin_url: str


class LinkedInBulkImportRequest(BaseModel):
    """Bulk import LinkedIn profiles request."""
    profiles: list[LinkedInProfileImport]


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
    
    # Normalize LinkedIn URL (remove query parameters)
    normalized_url = profile_data.linkedin_url.split('?')[0].rstrip('/')
    
    # Check if profile already exists (excluding soft-deleted)
    existing_query = select(Resume).where(
        Resume.linkedin_url == normalized_url,
        Resume.status != 'deleted'
    )
    existing_result = await db.execute(existing_query)
    existing_resume = existing_result.scalar_one_or_none()
    
    if existing_resume:
        # Update the existing resume with new data
        logger.info(f"Updating existing profile: {normalized_url}")
        
        # Update with new data
        update_data = {
            "location": profile_data.location or existing_resume.location,
            "summary": profile_data.about or existing_resume.summary,
            "current_title": profile_data.headline or existing_resume.current_title,
            "years_experience": profile_data.years_experience or existing_resume.years_experience,
            "last_linkedin_sync": datetime.utcnow(),
        }
        
        # Update skills if provided
        if profile_data.skills:
            normalized_skills = [normalize_skill_for_storage(skill) for skill in profile_data.skills]
            if normalized_skills:
                update_data["skills"] = normalized_skills
        
        for key, value in update_data.items():
            setattr(existing_resume, key, value)
        
        await db.commit()
        await db.refresh(existing_resume)
        
        # Re-index in vector search
        try:
            from app.services.reindex_service import reindex_service
            await reindex_service.reindex_resume(db, existing_resume)
        except Exception as e:
            logger.error(f"Failed to reindex resume: {e}")
        
        return LinkedInImportResponse(
            success=True,
            candidate_id=existing_resume.id,
            message="Profile updated successfully",
            is_duplicate=True
        )
    
    try:
        # Parse LinkedIn data
        parser = LinkedInParser()
        parsed_data = await parser.parse_linkedin_data(profile_data.dict())
        
        # Create new resume
        resume_data = {
            "user_id": current_user.id,
            "first_name": parsed_data.get("first_name", ""),
            "last_name": parsed_data.get("last_name", ""),
            "email": profile_data.email or parsed_data.get("email", ""),  # Use email from Chrome extension if provided
            "phone": profile_data.phone or parsed_data.get("phone", ""),  # Use phone from Chrome extension if provided
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
        
        # Debug log the skills being stored
        logger.info(f"Storing skills for {resume_data['first_name']} {resume_data['last_name']}: {resume_data['skills']}")
        
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
                    "title": profile_data.headline,
                    "location": profile_data.location,
                    "skills": [normalize_skill_for_storage(skill) for skill in (profile_data.skills or [])]
                }
            )
            if embedding:
                resume.embedding = embedding
        
        await db.commit()
        
        # Log import history
        logger.info(f"Successfully imported LinkedIn profile: {profile_data.linkedin_url}")
        
        return LinkedInImportResponse(
            success=True,
            candidate_id=resume.id,
            message="Profile imported successfully",
            is_duplicate=False
        )
        
    except Exception as e:
        logger.error(f"Failed to import LinkedIn profile: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import profile: {str(e)}"
        )


@router.post("/check-exists")
async def check_profile_exists(
    request: LinkedInCheckExistsRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Check if a LinkedIn profile already exists in the database."""
    
    query = select(Resume).where(Resume.linkedin_url == request.linkedin_url)
    result = await db.execute(query)
    resume = result.scalar_one_or_none()
    
    return {
        "exists": resume is not None,
        "candidate_id": str(resume.id) if resume else None,
        "last_sync": resume.last_linkedin_sync.isoformat() if resume and resume.last_linkedin_sync else None
    }


@router.post("/bulk-import")
async def bulk_import_profiles(
    request: LinkedInBulkImportRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Bulk import multiple LinkedIn profiles."""
    
    results = {
        "total": len(request.profiles),
        "imported": 0,
        "duplicates": 0,
        "failed": 0,
        "details": []
    }
    
    for profile_data in request.profiles:
        try:
            result = await import_linkedin_profile(profile_data, db, current_user)
            
            if result.is_duplicate:
                results["duplicates"] += 1
            else:
                results["imported"] += 1
            
            results["details"].append({
                "linkedin_url": profile_data.linkedin_url,
                "success": True,
                "is_duplicate": result.is_duplicate,
                "candidate_id": result.candidate_id
            })
            
        except Exception as e:
            results["failed"] += 1
            results["details"].append({
                "linkedin_url": profile_data.linkedin_url,
                "success": False,
                "error": str(e)
            })
            logger.error(f"Failed to import {profile_data.linkedin_url}: {e}")
    
    return results


@router.post("/sync/{resume_id}")
async def sync_linkedin_profile(
    resume_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Sync an existing profile with latest LinkedIn data."""
    
    # Get resume
    resume = await crud_resume.get(db, id=resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if not resume.linkedin_url:
        raise HTTPException(
            status_code=400, 
            detail="Resume does not have a LinkedIn URL"
        )
    
    # TODO: Implement actual LinkedIn data fetching
    # For now, just update the sync timestamp
    resume.last_linkedin_sync = datetime.utcnow()
    await db.commit()
    
    return {
        "success": True,
        "message": "Profile sync completed",
        "last_sync": resume.last_linkedin_sync.isoformat()
    }


@router.get("/import-stats")
async def get_import_stats(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Get LinkedIn import statistics for the current user."""
    
    # Count total LinkedIn profiles
    total_query = select(Resume).where(
        Resume.user_id == current_user.id,
        Resume.linkedin_url.isnot(None)
    )
    total_result = await db.execute(total_query)
    total_profiles = len(total_result.scalars().all())
    
    # Count today's imports
    today = datetime.utcnow().date()
    today_query = select(Resume).where(
        Resume.user_id == current_user.id,
        Resume.linkedin_url.isnot(None),
        Resume.created_at >= today
    )
    today_result = await db.execute(today_query)
    today_imports = len(today_result.scalars().all())
    
    return {
        "total_linkedin_profiles": total_profiles,
        "imported_today": today_imports,
        "last_import": None  # TODO: Get from import history
    }