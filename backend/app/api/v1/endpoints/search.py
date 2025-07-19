"""Search endpoints for natural language queries."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.config import settings
from app.schemas.resume import ResumeSearchResult
from app.services.search import search_service
from app.services.analytics import analytics_service
from app.models import EventType

router = APIRouter()
logger = logging.getLogger(__name__)


class SearchQuery(BaseModel):
    """Search query model."""

    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(10, ge=1, le=50)
    filters: Optional[dict] = None


class SearchFilters(BaseModel):
    """Search filters model."""
    
    location: Optional[str] = None
    min_experience: Optional[int] = Field(None, ge=0, le=50)
    max_experience: Optional[int] = Field(None, ge=0, le=50)
    skills: Optional[List[str]] = Field(None, max_items=10)


class DetailedSearchQuery(BaseModel):
    """Detailed search query with structured filters."""
    
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(10, ge=1, le=50)
    filters: Optional[SearchFilters] = None


@router.post("/", response_model=List[ResumeSearchResult])
async def search_resumes(
    search_query: DetailedSearchQuery,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> List[ResumeSearchResult]:
    """
    Search resumes using natural language query.
    
    Example queries:
    - "Find me a senior Python developer with AWS experience"
    - "Show me frontend developers who know React and have worked at startups"
    - "I need a data scientist with ML experience and PhD"
    """
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service is not configured. Please set OPENAI_API_KEY."
        )
    
    # Convert filters to dict
    filters_dict = None
    if search_query.filters:
        filters_dict = search_query.filters.dict(exclude_none=True)
    
    # Debug logging
    logger.info(f"=== SEARCH DEBUG: Starting search ===")
    logger.info(f"Query: '{search_query.query}'")
    logger.info(f"Limit: {search_query.limit}")
    logger.info(f"Filters: {filters_dict}")
    
    # Perform search
    results = await search_service.search_resumes(
        db,
        query=search_query.query,
        limit=search_query.limit,
        filters=filters_dict
    )
    
    logger.info(f"Search returned {len(results)} results")
    
    # Track search analytics
    await analytics_service.track_event(
        db=db,
        event_type=EventType.SEARCH_PERFORMED,
        event_data={
            "query": search_query.query,
            "filters": filters_dict,
            "results_count": len(results),
            "has_results": len(results) > 0
        },
        user_id=current_user.id
    )
    
    # Convert to response format
    search_results = []
    for resume_data, score in results:
        # Generate highlights based on query
        highlights = []
        query_terms = search_query.query.lower().split()
        
        if resume_data.get("summary"):
            summary_lower = resume_data["summary"].lower()
            for term in query_terms:
                if term in summary_lower:
                    # Find sentence containing the term
                    sentences = resume_data["summary"].split('.')
                    for sentence in sentences:
                        if term in sentence.lower():
                            highlights.append(sentence.strip() + ".")
                            break
        
        # Create summary snippet
        summary_snippet = resume_data.get("summary", "")
        if len(summary_snippet) > 200:
            summary_snippet = summary_snippet[:197] + "..."
        
        search_result = ResumeSearchResult(
            id=resume_data["id"],
            first_name=resume_data["first_name"],
            last_name=resume_data["last_name"],
            current_title=resume_data.get("current_title"),
            location=resume_data.get("location"),
            years_experience=resume_data.get("years_experience"),
            skills=resume_data.get("skills", []),
            score=round(score, 3),
            highlights=highlights[:3],  # Limit to 3 highlights
            summary_snippet=summary_snippet
        )
        search_results.append(search_result)
    
    return search_results


@router.get("/similar/{resume_id}", response_model=List[ResumeSearchResult])
async def get_similar_resumes(
    resume_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
    limit: int = Query(5, ge=1, le=20)
) -> List[ResumeSearchResult]:
    """Get resumes similar to a given resume."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service is not configured. Please set OPENAI_API_KEY."
        )
    
    # Get similar resumes
    results = await search_service.get_similar_resumes(
        db,
        resume_id=resume_id,
        limit=limit
    )
    
    # Convert to response format
    search_results = []
    for resume_data, score in results:
        search_result = ResumeSearchResult(
            id=resume_data["id"],
            first_name=resume_data["first_name"],
            last_name=resume_data["last_name"],
            current_title=resume_data.get("current_title"),
            location=resume_data.get("location"),
            years_experience=resume_data.get("years_experience"),
            skills=resume_data.get("skills", []),
            score=round(score, 3),
            highlights=[],
            summary_snippet=f"Similar match with {round(score * 100, 1)}% similarity"
        )
        search_results.append(search_result)
    
    return search_results


class SearchSuggestion(BaseModel):
    """Search suggestion model."""
    query: str = Field(..., description="The suggested search query")
    count: int = Field(..., description="Number of matching candidates")
    confidence: float = Field(..., description="Confidence score of the suggestion")
    category: str = Field(..., description="Category of suggestion (role, skill, experience)")


@router.get("/suggestions", response_model=List[SearchSuggestion])
async def get_search_suggestions(
    q: str = Query(..., min_length=2, max_length=100, description="Partial search query"),
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> List[SearchSuggestion]:
    """
    Get intelligent search suggestions based on partial query.
    
    Returns suggestions with candidate counts and categories.
    """
    suggestions = await search_service.get_search_suggestions(db, q)
    return suggestions


class PopularTag(BaseModel):
    """Popular tag model."""
    name: str = Field(..., description="Tag name")
    count: int = Field(..., description="Number of candidates with this tag")
    category: str = Field(..., description="Tag category (skill, tool, framework)")


@router.get("/popular-tags", response_model=List[PopularTag])
async def get_popular_tags(
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
    limit: int = Query(30, ge=1, le=50, description="Maximum number of tags to return")
) -> List[PopularTag]:
    """
    Get popular skills and technologies from resumes.
    
    Returns the most common skills with their counts.
    """
    tags = await search_service.get_popular_tags(db, limit)
    return tags


class DebugSearchResponse(BaseModel):
    """Debug search response with detailed information."""
    query: str
    total_resumes: int
    resumes_with_skills: int
    skill_samples: List[dict]
    search_sql: str
    results_found: int
    sample_results: List[dict]


@router.get("/debug/search", response_model=DebugSearchResponse)
async def debug_search(
    q: str = Query(..., description="Search query to debug"),
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> DebugSearchResponse:
    """
    Debug endpoint to diagnose search issues.
    
    Returns detailed information about:
    - Total resumes in database
    - How many have skills
    - Sample of skills data
    - SQL query being executed
    - Results found
    """
    from sqlalchemy import select, func
    from app.models.resume import Resume
    
    # Count total resumes
    total_stmt = select(func.count(Resume.id)).where(
        Resume.status == 'active',
        Resume.parse_status == 'completed'
    )
    total_result = await db.execute(total_stmt)
    total_resumes = total_result.scalar() or 0
    
    # Count resumes with skills
    skills_stmt = select(func.count(Resume.id)).where(
        Resume.status == 'active',
        Resume.parse_status == 'completed',
        Resume.skills.isnot(None)
    )
    skills_result = await db.execute(skills_stmt)
    resumes_with_skills = skills_result.scalar() or 0
    
    # Get sample of skills data
    sample_stmt = select(
        Resume.id,
        Resume.first_name,
        Resume.last_name,
        Resume.skills,
        Resume.current_title
    ).where(
        Resume.skills.isnot(None)
    ).limit(5)
    
    sample_result = await db.execute(sample_stmt)
    skill_samples = []
    for row in sample_result:
        skill_samples.append({
            "id": str(row.id),
            "name": f"{row.first_name} {row.last_name}",
            "title": row.current_title,
            "skills": row.skills,
            "skills_type": type(row.skills).__name__,
            "skills_count": len(row.skills) if row.skills else 0
        })
    
    # Search for WebSphere specifically
    websphere_searches = [
        f'%"{q}"%',
        f'%{q}%',
        f'%{q.lower()}%',
        f'%{q.upper()}%',
        f'%{q.title()}%'
    ]
    
    # Try different search approaches
    search_results = []
    for search_pattern in websphere_searches:
        search_stmt = select(
            Resume.id,
            Resume.first_name,
            Resume.last_name,
            Resume.skills,
            func.cast(Resume.skills, String).label('skills_text')
        ).where(
            Resume.status == 'active',
            func.cast(Resume.skills, String).ilike(search_pattern)
        ).limit(3)
        
        result = await db.execute(search_stmt)
        for row in result:
            search_results.append({
                "pattern": search_pattern,
                "id": str(row.id),
                "name": f"{row.first_name} {row.last_name}",
                "skills": row.skills,
                "skills_as_text": row.skills_text,
                "found": True
            })
    
    # Also check raw text
    raw_text_stmt = select(func.count(Resume.id)).where(
        Resume.raw_text.ilike(f'%{q}%')
    )
    raw_text_result = await db.execute(raw_text_stmt)
    raw_text_count = raw_text_result.scalar() or 0
    
    return DebugSearchResponse(
        query=q,
        total_resumes=total_resumes,
        resumes_with_skills=resumes_with_skills,
        skill_samples=skill_samples,
        search_sql=f"CAST(skills AS TEXT) ILIKE '%{q}%'",
        results_found=len(search_results),
        sample_results=search_results + [{"raw_text_matches": raw_text_count}]
    )