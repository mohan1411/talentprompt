"""Debug endpoint to check skills data for Anil and Sunil."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, cast, String

from app.api import deps
from app.models.user import User
from app.models.resume import Resume

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/check-profiles", response_model=Dict[str, Any])
async def check_anil_sunil_profiles(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """Check Anil and Sunil profiles and their skills."""
    
    results = {}
    
    for first_name in ["Anil", "Sunil"]:
        # Find the profile
        stmt = select(Resume).where(
            Resume.first_name == first_name,
            Resume.last_name == "Narasimhappa"
        )
        result = await db.execute(stmt)
        resume = result.scalar_one_or_none()
        
        if resume:
            # Check raw skills data
            skills_data = {
                "id": str(resume.id),
                "name": f"{resume.first_name} {resume.last_name}",
                "current_title": resume.current_title,
                "skills": resume.skills,
                "skills_type": type(resume.skills).__name__,
                "has_websphere": False
            }
            
            # Check if WebSphere is in skills
            if resume.skills:
                if isinstance(resume.skills, list):
                    skills_data["has_websphere"] = any(
                        "websphere" in str(skill).lower() 
                        for skill in resume.skills if skill
                    )
                elif isinstance(resume.skills, str):
                    skills_data["has_websphere"] = "websphere" in resume.skills.lower()
            
            # Check raw text
            skills_data["websphere_in_raw_text"] = False
            if resume.raw_text:
                skills_data["websphere_in_raw_text"] = "websphere" in resume.raw_text.lower()
            
            # Check parsed data
            skills_data["websphere_in_parsed_data"] = False
            if resume.parsed_data and isinstance(resume.parsed_data, dict):
                parsed_str = str(resume.parsed_data).lower()
                skills_data["websphere_in_parsed_data"] = "websphere" in parsed_str
            
            results[first_name] = skills_data
        else:
            results[first_name] = {"error": "Profile not found"}
    
    # Also search for all profiles with WebSphere
    websphere_stmt = select(Resume).where(
        Resume.status == 'active',
        cast(Resume.skills, String).ilike('%websphere%')
    ).limit(10)
    
    websphere_result = await db.execute(websphere_stmt)
    websphere_profiles = websphere_result.scalars().all()
    
    results["profiles_with_websphere"] = [
        {
            "name": f"{r.first_name} {r.last_name}",
            "skills": r.skills
        }
        for r in websphere_profiles
    ]
    
    return results