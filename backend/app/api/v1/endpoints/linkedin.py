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
    
    # Normalize LinkedIn URL (remove query parameters and trailing slash)
    normalized_url = profile_data.linkedin_url.split('?')[0].rstrip('/')
    
    logger.info(f"Import attempt - Original URL: {profile_data.linkedin_url}")
    logger.info(f"Import attempt - Normalized URL: {normalized_url}")
    logger.info(f"Import attempt - User ID: {current_user.id}")
    logger.info(f"Import attempt - User Email: {current_user.email}")
    
    # DEBUG: Let's see what the query actually finds
    test_query = select(Resume).where(
        Resume.linkedin_url == normalized_url
    )
    test_result = await db.execute(test_query)
    all_with_url = test_result.scalars().all()
    logger.info(f"DEBUG - All resumes with URL {normalized_url}: {[(r.id, r.user_id, r.status) for r in all_with_url]}")
    logger.info(f"DEBUG - Current user ID type: {type(current_user.id)}, value: {current_user.id}")
    
    # Check if profile already exists for this user (excluding soft-deleted)
    # Ensure user_id is compared as string if needed
    user_id_to_check = str(current_user.id) if hasattr(current_user.id, '__str__') else current_user.id
    
    existing_query = select(Resume).where(
        Resume.linkedin_url == normalized_url,
        Resume.user_id == user_id_to_check,
        Resume.status != 'deleted'
    )
    
    logger.info(f"DEBUG - Query checking for user_id: {user_id_to_check}, URL: {normalized_url}, excluding status: deleted")
    existing_result = await db.execute(existing_query)
    existing_resume = existing_result.scalar_one_or_none()
    
    # If not found, also check without trailing slash
    if not existing_resume and not normalized_url.endswith('/'):
        existing_query2 = select(Resume).where(
            Resume.linkedin_url == normalized_url + '/',
            Resume.user_id == current_user.id,
            Resume.status != 'deleted'
        )
        existing_result2 = await db.execute(existing_query2)
        existing_resume = existing_result2.scalar_one_or_none()
        
    logger.info(f"Existing resume found: {existing_resume is not None}")
    
    if existing_resume:
        # Return 409 Conflict for duplicate profiles
        logger.info(f"Duplicate profile detected: {normalized_url}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This profile has already been imported"
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
        
        # Generate embedding for vector search - temporarily disabled
        # TODO: Fix async context issue
        # if profile_data.about or profile_data.headline:
        #     search_text = f"{profile_data.headline or ''} {profile_data.about or ''}"
        #     embedding = await vector_search.index_resume(
        #         resume_id=str(resume.id),
        #         text=search_text,
        #         metadata={
        #             "user_id": str(current_user.id),  # CRITICAL: Include user_id for security
        #             "name": f"{parsed_data.get('first_name', '')} {parsed_data.get('last_name', '')}",
        #             "title": profile_data.headline,
        #             "location": profile_data.location,
        #             "skills": [normalize_skill_for_storage(skill) for skill in (profile_data.skills or [])]
        #         }
        #     )
        #     if embedding:
        #         resume.embedding = embedding
        
        await db.commit()
        
        # Log import history
        logger.info(f"Successfully imported LinkedIn profile: {profile_data.linkedin_url} for user {current_user.id}")
        logger.info(f"New resume created - ID: {resume.id}, Name: {profile_data.name}")
        
        return LinkedInImportResponse(
            success=True,
            candidate_id=resume.id,
            message="Profile imported successfully",
            is_duplicate=False
        )
        
    except Exception as e:
        logger.error(f"Failed to import LinkedIn profile: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        
        await db.rollback()
        
        # Check if it's a unique constraint violation
        error_message = str(e)
        if "duplicate key value violates unique constraint" in error_message:
            # Log detailed information about the constraint violation
            logger.error(f"Constraint violation details: {error_message}")
            
            if "resumes_linkedin_url_key" in error_message:
                # Old global constraint - this is the problem!
                logger.error("CRITICAL: Old global unique constraint still exists on linkedin_url!")
                logger.error(f"Profile {normalized_url} already imported by another user")
                
                # Return a different status code to distinguish this case
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,  # Using 423 to indicate resource locked by another user
                    detail="This profile has been imported by another user. The system currently doesn't support multiple users importing the same profile due to a database constraint issue."
                )
            elif "resumes_user_id_linkedin_url_key" in error_message:
                # New constraint - this means our duplicate check failed somehow
                logger.error(f"Duplicate check failed but constraint caught it. URL: {normalized_url}, User: {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already imported this profile"
                )
            else:
                # Unknown constraint
                logger.error(f"Unknown constraint violation: {error_message}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This profile cannot be imported due to a constraint violation"
                )
        
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
    
    # Normalize the URL to match import logic
    normalized_url = request.linkedin_url.split('?')[0].rstrip('/')
    
    # Check for the current user's resumes only
    query = select(Resume).where(
        Resume.linkedin_url == normalized_url,
        Resume.user_id == current_user.id,
        Resume.status != 'deleted'
    )
    result = await db.execute(query)
    resume = result.scalar_one_or_none()
    
    # If not found, also check with trailing slash
    if not resume and not normalized_url.endswith('/'):
        query2 = select(Resume).where(
            Resume.linkedin_url == normalized_url + '/',
            Resume.user_id == current_user.id,
            Resume.status != 'deleted'
        )
        result2 = await db.execute(query2)
        resume = result2.scalar_one_or_none()
    
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
            
        except HTTPException as e:
            # Check if it's a duplicate (409 conflict)
            if e.status_code == status.HTTP_409_CONFLICT:
                results["duplicates"] += 1
                results["details"].append({
                    "linkedin_url": profile_data.linkedin_url,
                    "success": False,
                    "is_duplicate": True,
                    "error": str(e.detail)
                })
                logger.info(f"Duplicate profile: {profile_data.linkedin_url}")
            else:
                results["failed"] += 1
                results["details"].append({
                    "linkedin_url": profile_data.linkedin_url,
                    "success": False,
                    "error": str(e.detail)
                })
                logger.error(f"Failed to import {profile_data.linkedin_url}: {e}")
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