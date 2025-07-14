"""Search endpoints for natural language queries."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.config import settings
from app.schemas.resume import ResumeSearchResult
from app.services.search import search_service

router = APIRouter()


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
    
    # Perform search
    results = await search_service.search_resumes(
        db,
        query=search_query.query,
        limit=search_query.limit,
        filters=filters_dict
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