"""Debug endpoints for search functionality."""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, String, cast, or_, text

from app.api import deps
from app.models.user import User
from app.models.resume import Resume
from app.services.search_skill_fix import create_skill_search_conditions

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/check-skills")
async def check_skills_data(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Check skills data in the database."""
    
    # Count resumes with skills
    count_result = await db.execute(
        select(func.count(Resume.id)).where(
            Resume.skills.isnot(None)
        )
    )
    total_with_skills = count_result.scalar()
    
    # Get sample resumes with skills
    sample_result = await db.execute(
        select(Resume.id, Resume.first_name, Resume.last_name, Resume.skills, Resume.linkedin_url)
        .where(Resume.skills.isnot(None))
        .limit(10)
    )
    samples = sample_result.all()
    
    # Check for WebSphere specifically
    websphere_results = {}
    variations = ['WebSphere', 'websphere', 'Websphere', 'WEBSPHERE', 'web sphere']
    
    for variation in variations:
        # Simple ILIKE check
        count_result = await db.execute(
            select(func.count(Resume.id)).where(
                cast(Resume.skills, String).ilike(f'%{variation}%')
            )
        )
        websphere_results[variation] = count_result.scalar()
    
    # Check Anil's profile
    anil_result = await db.execute(
        select(Resume)
        .where(Resume.linkedin_url.like('%anil-narasimhappa%'))
        .limit(1)
    )
    anil = anil_result.scalar_one_or_none()
    
    # Raw SQL check
    raw_result = await db.execute(
        text("""
            SELECT COUNT(*) 
            FROM resumes 
            WHERE skills::text ILIKE '%websphere%' 
            OR skills::text ILIKE '%WebSphere%'
        """)
    )
    raw_count = raw_result.scalar()
    
    return {
        "total_resumes_with_skills": total_with_skills,
        "sample_resumes": [
            {
                "id": str(s.id),
                "name": f"{s.first_name} {s.last_name}",
                "skills": s.skills,
                "linkedin_url": s.linkedin_url
            }
            for s in samples
        ],
        "websphere_counts": websphere_results,
        "anil_profile": {
            "found": anil is not None,
            "skills": anil.skills if anil else None,
            "id": str(anil.id) if anil else None
        },
        "raw_sql_websphere_count": raw_count
    }


@router.get("/test-search")
async def test_search(
    query: str = Query(..., description="Search query"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Test search functionality with detailed debug info."""
    
    # Create search conditions
    conditions = create_skill_search_conditions(query, Resume)
    
    # Execute search
    result = await db.execute(
        select(Resume.id, Resume.first_name, Resume.last_name, Resume.skills, Resume.current_title)
        .where(or_(*conditions))
        .limit(10)
    )
    search_results = result.all()
    
    # Also try simple ILIKE
    simple_result = await db.execute(
        select(Resume.id, Resume.first_name, Resume.last_name, Resume.skills)
        .where(
            or_(
                cast(Resume.skills, String).ilike(f'%{query}%'),
                Resume.raw_text.ilike(f'%{query}%'),
                Resume.current_title.ilike(f'%{query}%')
            )
        )
        .limit(10)
    )
    simple_results = simple_result.all()
    
    return {
        "query": query,
        "num_conditions": len(conditions),
        "search_results": [
            {
                "id": str(r.id),
                "name": f"{r.first_name} {r.last_name}",
                "skills": r.skills,
                "title": r.current_title
            }
            for r in search_results
        ],
        "simple_search_results": [
            {
                "id": str(r.id),
                "name": f"{r.first_name} {r.last_name}",
                "skills": r.skills
            }
            for r in simple_results
        ]
    }