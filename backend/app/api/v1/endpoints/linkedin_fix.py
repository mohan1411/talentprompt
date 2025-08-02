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


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify the router is working."""
    return {"status": "ok", "message": "LinkedIn fix endpoint is working"}


@router.post("/simple-import", response_model=LinkedInImportResponse)
async def simple_linkedin_import(
    profile_data: LinkedInProfileImport,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> LinkedInImportResponse:
    """Simplified LinkedIn import that just updates or creates without complex checks."""
    
    # Normalize URL
    normalized_url = profile_data.linkedin_url.split('?')[0].rstrip('/')
    logger.info(f"Simple import for: {normalized_url}")
    
    try:
        # Very simple query - just check exact match
        stmt = select(Resume).where(
            Resume.linkedin_url == normalized_url,
            Resume.user_id == current_user.id
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update
            existing.location = profile_data.location or existing.location
            existing.summary = profile_data.about or existing.summary
            existing.current_title = profile_data.headline or existing.current_title
            existing.years_experience = profile_data.years_experience or existing.years_experience
            if profile_data.skills:
                existing.skills = [normalize_skill_for_storage(s) for s in profile_data.skills]
            
            # Update linkedin data
            existing.linkedin_data = profile_data.dict()
            existing.last_linkedin_sync = datetime.utcnow()
            existing.updated_at = datetime.utcnow()
            
            # Ensure status is active
            if existing.status == 'deleted':
                existing.status = 'active'
            
            # Re-index in vector search
            if existing.summary or existing.current_title:
                try:
                    search_text = f"{existing.current_title or ''} {existing.summary or ''}"
                    await vector_search.index_resume(
                        resume_id=str(existing.id),
                        text=search_text,
                        metadata={
                            "user_id": str(current_user.id),  # CRITICAL: Include user_id for security
                            "name": f"{existing.first_name} {existing.last_name}",
                            "skills": existing.skills or [],
                            "location": existing.location or "",
                            "years_experience": existing.years_experience or 0
                        }
                    )
                    logger.info(f"Successfully re-indexed resume {existing.id}")
                except Exception as e:
                    logger.error(f"Failed to reindex resume: {e}")
            
            await db.commit()
            
            return LinkedInImportResponse(
                success=True,
                candidate_id=existing.id,
                message="Profile updated",
                is_duplicate=True
            )
        else:
            # Parse name
            first_name = "Unknown"
            last_name = "Profile"
            if profile_data.name:
                name_parts = profile_data.name.strip().split()
                if name_parts:
                    first_name = name_parts[0]
                    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            # Build raw text for searching
            raw_text_parts = []
            if profile_data.name:
                raw_text_parts.append(profile_data.name)
            if profile_data.headline:
                raw_text_parts.append(profile_data.headline)
            if profile_data.about:
                raw_text_parts.append(profile_data.about)
            if profile_data.skills:
                raw_text_parts.append("Skills: " + ", ".join(profile_data.skills))
            
            raw_text = "\n\n".join(raw_text_parts)
            
            # Create parsed data
            parsed_data = {
                "first_name": first_name,
                "last_name": last_name,
                "experience": profile_data.experience or [],
                "education": profile_data.education or [],
                "skills": profile_data.skills or [],
                "parsed_at": datetime.utcnow().isoformat()
            }
            
            # Create new
            resume = Resume(
                user_id=current_user.id,
                first_name=first_name,
                last_name=last_name,
                email=profile_data.email or "",
                phone=profile_data.phone or "",
                location=profile_data.location or "",
                summary=profile_data.about or "",
                current_title=profile_data.headline or "",
                years_experience=profile_data.years_experience or 0,
                skills=[normalize_skill_for_storage(s) for s in (profile_data.skills or [])],
                keywords=[],
                linkedin_url=normalized_url,
                linkedin_data=profile_data.dict(),
                raw_text=raw_text,
                parsed_data=parsed_data,
                status="active",
                parse_status="completed",
                parsed_at=datetime.utcnow(),
                last_linkedin_sync=datetime.utcnow()
            )
            
            db.add(resume)
            await db.flush()
            
            # Index in vector search
            if raw_text:
                try:
                    await vector_search.index_resume(
                        resume_id=str(resume.id),
                        text=raw_text,
                        metadata={
                            "user_id": str(current_user.id),  # CRITICAL: Include user_id for security
                            "name": f"{first_name} {last_name}",
                            "skills": resume.skills or [],
                            "location": resume.location or "",
                            "years_experience": resume.years_experience or 0
                        }
                    )
                    logger.info(f"Successfully indexed resume {resume.id} in vector search")
                except Exception as e:
                    logger.error(f"Failed to index resume in vector search: {e}")
            
            await db.commit()
            
            return LinkedInImportResponse(
                success=True,
                candidate_id=resume.id,
                message="Profile created",
                is_duplicate=False
            )
            
    except Exception as e:
        logger.error(f"Simple import error: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


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
    
    # Simple check for exact match first
    try:
        result = await db.execute(
            select(Resume).where(
                Resume.linkedin_url == normalized_url,
                Resume.status != 'deleted'
            )
        )
        existing_resume = result.scalar_one_or_none()
        
        # If not found, check with trailing slash
        if not existing_resume:
            result = await db.execute(
                select(Resume).where(
                    Resume.linkedin_url == normalized_url + '/',
                    Resume.status != 'deleted'
                )
            )
            existing_resume = result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error checking for existing resume: {e}")
        # Continue without existing check - will fail on insert if duplicate
    
    # If exists but belongs to different user, we have a problem
    if existing_resume and existing_resume.user_id != current_user.id:
        raise HTTPException(
            status_code=400,
            detail="This LinkedIn profile has already been imported by another user"
        )
    
    # Log what we found
    if existing_resume:
        logger.info(f"Found existing resume ID: {existing_resume.id} with URL: {existing_resume.linkedin_url}")
    else:
        logger.info(f"No existing resume found for URL: {normalized_url}")
    
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
            
            # Re-index in vector search
            try:
                if existing_resume.summary or existing_resume.current_title:
                    search_text = f"{existing_resume.current_title or ''} {existing_resume.summary or ''}"
                    await vector_search.index_resume(
                        resume_id=str(existing_resume.id),
                        text=search_text,
                        metadata={
                            "user_id": str(current_user.id),  # CRITICAL: Include user_id for security
                            "name": f"{existing_resume.first_name} {existing_resume.last_name}",
                            "skills": existing_resume.skills or [],
                            "location": existing_resume.location or "",
                            "years_experience": existing_resume.years_experience or 0
                        }
                    )
                    logger.info(f"Successfully re-indexed resume {existing_resume.id}")
            except Exception as e:
                logger.error(f"Failed to reindex resume: {e}")
            
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
                try:
                    embedding = await vector_search.index_resume(
                        resume_id=str(resume.id),
                        text=search_text,
                        metadata={
                            "user_id": str(current_user.id),  # CRITICAL: Include user_id for security
                            "name": f"{parsed_data.get('first_name', '')} {parsed_data.get('last_name', '')}",
                            "skills": resume_data['skills'],
                            "location": resume_data['location'],
                            "years_experience": resume_data['years_experience']
                        }
                    )
                    logger.info(f"Successfully indexed resume {resume.id} in vector search")
                except Exception as e:
                    logger.error(f"Failed to index resume in vector search: {e}")
                    # Continue without vector search - profile is still saved
            
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