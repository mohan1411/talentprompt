"""One-time data fix endpoint."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.models.user import User
from app.models.resume import Resume

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/fix-anil-skills", response_model=Dict[str, Any])
async def fix_anil_skills(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """Fix Anil's missing WebSphere skills."""
    
    # Find Anil's profile
    stmt = select(Resume).where(
        Resume.first_name == "Anil",
        Resume.last_name == "Narasimhappa"
    )
    result = await db.execute(stmt)
    anil = result.scalar_one_or_none()
    
    if not anil:
        raise HTTPException(status_code=404, detail="Anil Narasimhappa not found")
    
    # Store current skills for comparison
    old_skills = anil.skills or []
    
    # Update skills to include WebSphere technologies
    new_skills = [
        "WebSphere",
        "WebSphere Application Server",
        "WebSphere Message Broker",
        "IBM MQ",
        "Java",
        "J2EE",
        "Enterprise Integration",
        "Middleware",
        "SOA",
        "Web Services"
    ]
    
    # Preserve any existing skills that aren't duplicates
    for skill in old_skills:
        if skill and skill not in new_skills:
            new_skills.append(skill)
    
    anil.skills = new_skills
    
    await db.commit()
    await db.refresh(anil)
    
    return {
        "success": True,
        "message": "Successfully updated Anil's skills",
        "old_skills": old_skills,
        "new_skills": anil.skills,
        "profile": {
            "id": str(anil.id),
            "name": f"{anil.first_name} {anil.last_name}",
            "current_title": anil.current_title
        }
    }


@router.post("/reindex-anil", response_model=Dict[str, Any])
async def reindex_anil(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """Re-index Anil's profile in vector search."""
    
    # Import here to avoid circular dependency
    from app.services.vector_search import vector_search
    
    # Find Anil's profile
    stmt = select(Resume).where(
        Resume.first_name == "Anil",
        Resume.last_name == "Narasimhappa"
    )
    result = await db.execute(stmt)
    anil = result.scalar_one_or_none()
    
    if not anil:
        raise HTTPException(status_code=404, detail="Anil Narasimhappa not found")
    
    # Create search text from profile
    search_text = f"{anil.current_title or ''} {anil.summary or ''} {' '.join(anil.skills or [])}"
    
    # Re-index in vector search
    try:
        embedding = await vector_search.index_resume(
            resume_id=str(anil.id),
            text=search_text,
            metadata={
                "name": f"{anil.first_name} {anil.last_name}",
                "title": anil.current_title,
                "location": anil.location,
                "skills": anil.skills or []
            }
        )
        
        # Update embedding in database
        if embedding:
            anil.embedding = embedding
            await db.commit()
        
        return {
            "success": True,
            "message": "Successfully re-indexed Anil's profile",
            "profile": {
                "id": str(anil.id),
                "name": f"{anil.first_name} {anil.last_name}",
                "skills": anil.skills,
                "indexed_text_preview": search_text[:200] + "..."
            }
        }
    except Exception as e:
        logger.error(f"Failed to re-index: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/verify-fix", response_model=Dict[str, Any])
async def verify_fix(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """Verify the fix was applied."""
    
    # Check Anil's skills
    stmt = select(Resume).where(
        Resume.first_name == "Anil",
        Resume.last_name == "Narasimhappa"
    )
    result = await db.execute(stmt)
    anil = result.scalar_one_or_none()
    
    if not anil:
        return {"error": "Anil not found"}
    
    has_websphere = any("websphere" in str(s).lower() for s in (anil.skills or []) if s)
    
    return {
        "profile": f"{anil.first_name} {anil.last_name}",
        "skills": anil.skills,
        "has_websphere": has_websphere,
        "websphere_skills": [s for s in (anil.skills or []) if s and "websphere" in s.lower()]
    }