"""Debug endpoint specifically for WebSphere search issue."""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.resume import ResumeSearchResult
from app.services.search import search_service
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/websphere", response_model=List[ResumeSearchResult])
async def debug_websphere_search(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> List[ResumeSearchResult]:
    """
    Debug endpoint specifically for WebSphere search.
    This mimics the exact search that would happen from the UI.
    """
    logger.info("=== DEBUG WEBSPHERE SEARCH ===")
    
    # Perform the exact same search as the main search endpoint
    results = await search_service.search_resumes(
        db=db,
        query="WebSphere",
        limit=10
    )
    
    # Log detailed results
    logger.info(f"Search returned {len(results)} results")
    for i, (resume_data, score) in enumerate(results):
        logger.info(f"{i+1}. {resume_data['first_name']} {resume_data['last_name']} - Score: {score}")
        logger.info(f"   Skills: {resume_data.get('skills', [])}")
        logger.info(f"   Has WebSphere in skills: {any('websphere' in str(s).lower() for s in resume_data.get('skills', []))}")
    
    # Format for API response
    search_results = []
    for resume_data, score in results:
        # Extract highlights
        highlights = []
        query_lower = "websphere"
        
        # Check for matches in various fields
        if resume_data.get("summary"):
            summary_lower = resume_data["summary"].lower()
            if query_lower in summary_lower:
                # Find sentences containing the query
                sentences = resume_data["summary"].split('.')
                for sentence in sentences:
                    if query_lower in sentence.lower():
                        highlights.append(sentence.strip() + ".")
                        if len(highlights) >= 3:
                            break
        
        # Check skills for highlights
        if resume_data.get("skills"):
            for skill in resume_data["skills"]:
                if skill and query_lower in skill.lower():
                    highlights.append(f"Skill: {skill}")
        
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


@router.get("/compare-searches")
async def compare_search_methods(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """Compare different search methods for WebSphere."""
    
    # 1. Main search service
    main_results = await search_service.search_resumes(db, "WebSphere", limit=5)
    
    # 2. Direct vector search
    from app.services.vector_search import vector_search
    vector_results = []
    try:
        vr = await vector_search.search_similar("WebSphere", limit=5)
        vector_results = vr if vr else []
    except Exception as e:
        vector_results = [{"error": str(e)}]
    
    # 3. Direct keyword search
    keyword_results = await search_service._keyword_search(db, "WebSphere", limit=5)
    
    return {
        "main_search_results": [
            {
                "name": f"{r[0]['first_name']} {r[0]['last_name']}",
                "score": r[1],
                "skills": r[0].get('skills', [])
            }
            for r in main_results
        ],
        "vector_search_results": vector_results[:5] if isinstance(vector_results, list) else vector_results,
        "keyword_search_results": [
            {
                "name": f"{r[0]['first_name']} {r[0]['last_name']}",
                "score": r[1],
                "skills": r[0].get('skills', [])
            }
            for r in keyword_results
        ]
    }