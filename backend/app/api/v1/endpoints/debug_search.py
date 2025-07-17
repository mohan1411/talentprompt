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
    
    # Count total resumes
    total_result = await db.execute(
        select(func.count(Resume.id))
    )
    total_resumes = total_result.scalar()
    
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
    
    # Also get ALL LinkedIn imported resumes
    linkedin_result = await db.execute(
        select(Resume.id, Resume.first_name, Resume.last_name, Resume.skills, Resume.linkedin_url)
        .where(Resume.linkedin_url.isnot(None))
        .limit(20)
    )
    linkedin_resumes = linkedin_result.all()
    
    return {
        "total_resumes": total_resumes,
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
        "linkedin_imported_resumes": [
            {
                "id": str(l.id),
                "name": f"{l.first_name} {l.last_name}",
                "skills": l.skills,
                "linkedin_url": l.linkedin_url
            }
            for l in linkedin_resumes
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


@router.get("/test-suggestions")
async def test_suggestions(
    query: str = Query(..., description="Search query for suggestions"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Test search suggestions functionality."""
    from app.services.search import search_service
    
    suggestions = await search_service.get_search_suggestions(db, query)
    
    # Manual count for the query in different fields
    manual_counts = {}
    
    # Count in skills array
    skills_count = await db.execute(
        select(func.count(Resume.id)).where(
            cast(Resume.skills, String).ilike(f'%{query}%')
        )
    )
    manual_counts['in_skills'] = skills_count.scalar()
    
    # Count in raw text
    text_count = await db.execute(
        select(func.count(Resume.id)).where(
            Resume.raw_text.ilike(f'%{query}%')
        )
    )
    manual_counts['in_raw_text'] = text_count.scalar()
    
    # Count in title
    title_count = await db.execute(
        select(func.count(Resume.id)).where(
            Resume.current_title.ilike(f'%{query}%')
        )
    )
    manual_counts['in_title'] = title_count.scalar()
    
    # Try to find matching skills directly using JSON extraction
    matching_skills = []
    try:
        skills_result = await db.execute(
            text("""
                SELECT DISTINCT skill, COUNT(*) as count
                FROM resumes, jsonb_array_elements_text(skills::jsonb) as skill
                WHERE LOWER(skill) LIKE LOWER(:query)
                GROUP BY skill
                ORDER BY count DESC
                LIMIT 10
            """),
            {"query": f"%{query}%"}
        )
        matching_skills = [{"skill": s[0], "count": s[1]} for s in skills_result.all()]
    except Exception as e:
        logger.error(f"Error extracting skills: {e}")
        matching_skills = [{"error": str(e)}]
    
    # Get sample of actual skills data to see format
    sample_skills = await db.execute(
        select(Resume.skills)
        .where(Resume.skills.isnot(None))
        .limit(5)
    )
    sample_data = [s[0] for s in sample_skills.all()]
    
    return {
        "query": query,
        "suggestions": suggestions,
        "manual_counts": manual_counts,
        "matching_skills_in_db": matching_skills,
        "sample_skills_format": sample_data[:3]  # Show format of skills in DB
    }


@router.get("/verify-skills-format")
async def verify_skills_format(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Verify the format of skills data in the database."""
    
    # Get different types of skills data
    results = {}
    
    # 1. Check if skills column is JSON/JSONB
    try:
        type_check = await db.execute(
            text("""
                SELECT column_name, data_type, udt_name
                FROM information_schema.columns
                WHERE table_name = 'resumes' AND column_name = 'skills'
            """)
        )
        column_info = type_check.first()
        results["column_type"] = dict(column_info) if column_info else None
    except Exception as e:
        results["column_type_error"] = str(e)
    
    # 2. Get sample of raw skills data
    try:
        raw_sample = await db.execute(
            text("SELECT id, skills::text FROM resumes WHERE skills IS NOT NULL LIMIT 5")
        )
        results["raw_samples"] = [
            {"id": str(r[0]), "skills_text": r[1][:200]} 
            for r in raw_sample.all()
        ]
    except Exception as e:
        results["raw_samples_error"] = str(e)
    
    # 3. Test JSON extraction
    try:
        json_test = await db.execute(
            text("""
                SELECT COUNT(*)
                FROM resumes, jsonb_array_elements_text(skills::jsonb) as skill
                WHERE skills IS NOT NULL
            """)
        )
        results["json_extraction_works"] = True
        results["total_skills_extracted"] = json_test.scalar()
    except Exception as e:
        results["json_extraction_works"] = False
        results["json_extraction_error"] = str(e)
    
    # 4. Find all unique skills
    try:
        unique_skills = await db.execute(
            text("""
                SELECT DISTINCT skill
                FROM resumes, jsonb_array_elements_text(skills::jsonb) as skill
                ORDER BY skill
                LIMIT 50
            """)
        )
        results["unique_skills_sample"] = [s[0] for s in unique_skills.all()]
    except Exception as e:
        results["unique_skills_error"] = str(e)
    
    # 5. Check for specific skills
    test_skills = ["people development", "workshops", "WebSphere"]
    results["specific_skill_checks"] = {}
    
    for skill in test_skills:
        try:
            count = await db.execute(
                text("""
                    SELECT COUNT(DISTINCT resume_id)
                    FROM (
                        SELECT id as resume_id
                        FROM resumes, jsonb_array_elements_text(skills::jsonb) as skill
                        WHERE LOWER(skill) LIKE LOWER(:pattern)
                    ) as matches
                """),
                {"pattern": f"%{skill}%"}
            )
            results["specific_skill_checks"][skill] = count.scalar()
        except Exception as e:
            results["specific_skill_checks"][skill] = f"Error: {e}"
    
    return results


@router.get("/check-profile/{linkedin_username}")
async def check_profile(
    linkedin_username: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Check a specific profile by LinkedIn username."""
    
    # Search for the profile
    profile_result = await db.execute(
        select(Resume)
        .where(Resume.linkedin_url.like(f'%{linkedin_username}%'))
        .limit(1)
    )
    profile = profile_result.scalar_one_or_none()
    
    if not profile:
        return {
            "found": False,
            "linkedin_username": linkedin_username,
            "message": "Profile not found in database"
        }
    
    # Extract skills if they exist
    skills_list = []
    if profile.skills:
        if isinstance(profile.skills, list):
            skills_list = profile.skills
        elif isinstance(profile.skills, str):
            try:
                import json
                skills_list = json.loads(profile.skills)
            except:
                skills_list = [profile.skills]
    
    # Check for specific skills
    expected_skills = ["Kaizen", "Strategy", "Employee Training", "Project Management"]
    found_skills = {}
    missing_skills = []
    
    for expected_skill in expected_skills:
        found = False
        for skill in skills_list:
            if expected_skill.lower() in skill.lower():
                found = True
                found_skills[expected_skill] = skill
                break
        if not found:
            missing_skills.append(expected_skill)
    
    # Also check in raw_text
    raw_text_checks = {}
    if profile.raw_text:
        for skill in expected_skills:
            raw_text_checks[skill] = skill.lower() in profile.raw_text.lower()
    
    return {
        "found": True,
        "profile": {
            "id": str(profile.id),
            "name": f"{profile.first_name} {profile.last_name}",
            "linkedin_url": profile.linkedin_url,
            "current_title": profile.current_title,
            "skills_count": len(skills_list),
            "skills": skills_list,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
        },
        "skill_analysis": {
            "expected_skills": expected_skills,
            "found_skills": found_skills,
            "missing_skills": missing_skills,
            "skills_in_raw_text": raw_text_checks
        },
        "raw_data": {
            "skills_type": type(profile.skills).__name__,
            "skills_raw": str(profile.skills)[:500] if profile.skills else None,
            "has_raw_text": profile.raw_text is not None
        }
    }