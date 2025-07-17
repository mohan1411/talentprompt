"""Debug endpoint to check profile data for Sunil and Anil."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, cast, String

from app.api import deps
from app.models.user import User
from app.models.resume import Resume

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/check-narasimhappa-profiles")
async def check_narasimhappa_profiles(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Check both Narasimhappa profiles and their skills."""
    
    # Find both profiles
    result = await db.execute(
        select(Resume)
        .where(
            or_(
                Resume.last_name.ilike('%narasimhappa%'),
                Resume.linkedin_url.ilike('%narasimhappa%')
            )
        )
    )
    profiles = result.scalars().all()
    
    profile_data = []
    websphere_profiles = []
    
    for profile in profiles:
        data = {
            "id": str(profile.id),
            "name": f"{profile.first_name} {profile.last_name}",
            "linkedin_url": profile.linkedin_url,
            "skills": profile.skills,
            "current_title": profile.current_title,
            "summary_snippet": profile.summary[:200] if profile.summary else None
        }
        profile_data.append(data)
        
        # Check if this profile has WebSphere
        if profile.skills:
            skills_text = str(profile.skills).lower()
            if 'websphere' in skills_text:
                websphere_profiles.append({
                    "name": f"{profile.first_name} {profile.last_name}",
                    "has_websphere": True,
                    "skills_containing_websphere": [s for s in profile.skills if 'websphere' in s.lower()]
                })
    
    # Also check raw_text for WebSphere mentions
    websphere_in_text = []
    for profile in profiles:
        if profile.raw_text and 'websphere' in profile.raw_text.lower():
            websphere_in_text.append({
                "name": f"{profile.first_name} {profile.last_name}",
                "websphere_mentions": profile.raw_text.lower().count('websphere')
            })
    
    return {
        "total_narasimhappa_profiles": len(profiles),
        "profiles": profile_data,
        "websphere_profiles": websphere_profiles,
        "websphere_in_raw_text": websphere_in_text
    }


@router.get("/search-websphere-debug")
async def search_websphere_debug(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Debug WebSphere search to see why wrong profile is returned."""
    
    # Search for WebSphere in different ways
    results = {}
    
    # 1. Simple skills search
    skill_search = await db.execute(
        select(Resume.id, Resume.first_name, Resume.last_name, Resume.skills)
        .where(cast(Resume.skills, String).ilike('%websphere%'))
        .limit(10)
    )
    results["skills_search"] = [
        {
            "id": str(r.id),
            "name": f"{r.first_name} {r.last_name}",
            "skills": r.skills
        }
        for r in skill_search.all()
    ]
    
    # 2. Raw text search
    text_search = await db.execute(
        select(Resume.id, Resume.first_name, Resume.last_name)
        .where(Resume.raw_text.ilike('%websphere%'))
        .limit(10)
    )
    results["raw_text_search"] = [
        {
            "id": str(r.id),
            "name": f"{r.first_name} {r.last_name}"
        }
        for r in text_search.all()
    ]
    
    # 3. Check vector search results
    from app.services.search import search_service
    
    vector_results = await search_service.search_resumes(db, "WebSphere", limit=5)
    results["vector_search_results"] = [
        {
            "name": f"{r['first_name']} {r['last_name']}",
            "score": r.get('score', 0),
            "skills": r.get('skills', [])
        }
        for r, _ in vector_results
    ]
    
    return results