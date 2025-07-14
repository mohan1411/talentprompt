"""Search service using Qdrant vector database."""

import logging
import re
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.resume import Resume
from app.services.vector_search import vector_search

logger = logging.getLogger(__name__)


class SearchService:
    """Service for performing vector similarity search on resumes."""
    
    async def search_resumes(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 10,
        filters: Optional[dict] = None
    ) -> List[Tuple[dict, float]]:
        """Search resumes using vector similarity with Qdrant.
        
        Args:
            db: Database session
            query: Search query text
            limit: Maximum number of results
            filters: Optional filters (location, skills, experience)
            
        Returns:
            List of tuples (resume_data, similarity_score)
        """
        try:
            # First, try vector search with Qdrant
            vector_results = await vector_search.search_similar(
                query=query,
                limit=limit * 2,  # Get more results to filter
                filters=filters
            )
            
            if vector_results:
                # Get resume IDs from vector search
                resume_ids = [r["resume_id"] for r in vector_results]
                
                # Fetch full resume data from PostgreSQL
                stmt = select(Resume).where(Resume.id.in_(resume_ids))
                result = await db.execute(stmt)
                resumes = {str(r.id): r for r in result.scalars().all()}
                
                # Combine results with scores
                search_results = []
                for vr in vector_results:
                    resume_id = vr["resume_id"]
                    if resume_id in resumes:
                        resume = resumes[resume_id]
                        resume_data = {
                            "id": str(resume.id),
                            "first_name": resume.first_name,
                            "last_name": resume.last_name,
                            "email": resume.email,
                            "phone": resume.phone,
                            "location": resume.location,
                            "current_title": resume.current_title,
                            "summary": resume.summary,
                            "years_experience": resume.years_experience,
                            "skills": resume.skills or [],
                            "keywords": resume.keywords or [],
                            "created_at": resume.created_at,
                            "view_count": resume.view_count or 0
                        }
                        search_results.append((resume_data, vr["score"]))
                
                return search_results[:limit]
                
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            # Fall back to keyword search
        
        # Fallback: Keyword-based search using PostgreSQL
        return await self._keyword_search(db, query, limit, filters)
    
    async def _keyword_search(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 10,
        filters: Optional[dict] = None
    ) -> List[Tuple[dict, float]]:
        """Fallback keyword search using PostgreSQL."""
        # Build query
        stmt = select(Resume).where(
            Resume.status == 'active',
            Resume.parse_status == 'completed'
        )
        
        # Add keyword search
        search_terms = query.lower().split()
        if search_terms:
            search_conditions = []
            for term in search_terms:
                term_pattern = f"%{term}%"
                search_conditions.append(
                    or_(
                        Resume.summary.ilike(term_pattern),
                        Resume.current_title.ilike(term_pattern),
                        Resume.raw_text.ilike(term_pattern)
                    )
                )
            stmt = stmt.where(or_(*search_conditions))
        
        # Add filters
        if filters:
            if filters.get("location"):
                stmt = stmt.where(Resume.location.ilike(f"%{filters['location']}%"))
            
            if filters.get("min_experience"):
                stmt = stmt.where(Resume.years_experience >= filters["min_experience"])
            
            if filters.get("max_experience"):
                stmt = stmt.where(Resume.years_experience <= filters["max_experience"])
            
            if filters.get("skills"):
                # For each skill, check if it exists in the skills JSON array
                for skill in filters["skills"]:
                    stmt = stmt.where(
                        Resume.skills.contains([skill])
                    )
        
        # Execute query
        result = await db.execute(stmt.limit(limit))
        resumes = result.scalars().all()
        
        # Format results with basic scoring
        search_results = []
        for resume in resumes:
            # Calculate basic relevance score
            score = 0.5  # Base score
            
            # Boost score for term matches
            for term in search_terms:
                if term in (resume.summary or "").lower():
                    score += 0.1
                if term in (resume.current_title or "").lower():
                    score += 0.2
            
            resume_data = {
                "id": str(resume.id),
                "first_name": resume.first_name,
                "last_name": resume.last_name,
                "email": resume.email,
                "phone": resume.phone,
                "location": resume.location,
                "current_title": resume.current_title,
                "summary": resume.summary,
                "years_experience": resume.years_experience,
                "skills": resume.skills or [],
                "keywords": resume.keywords or [],
                "created_at": resume.created_at,
                "view_count": resume.view_count or 0
            }
            search_results.append((resume_data, min(score, 1.0)))
        
        # Sort by score
        search_results.sort(key=lambda x: x[1], reverse=True)
        
        return search_results
    
    async def get_similar_resumes(
        self,
        db: AsyncSession,
        resume_id: str,
        limit: int = 5
    ) -> List[Tuple[dict, float]]:
        """Find similar resumes to a given resume."""
        # Get the resume
        stmt = select(Resume).where(Resume.id == resume_id)
        result = await db.execute(stmt)
        resume = result.scalar_one_or_none()
        
        if not resume:
            return []
        
        # Build a query from resume content
        query_parts = []
        if resume.current_title:
            query_parts.append(resume.current_title)
        if resume.skills:
            query_parts.extend(resume.skills[:5])  # Top 5 skills
        
        if not query_parts:
            return []
        
        query = " ".join(query_parts)
        
        # Search for similar resumes
        results = await self.search_resumes(db, query, limit + 1)
        
        # Filter out the original resume
        return [(r, s) for r, s in results if r["id"] != str(resume_id)][:limit]


# Create singleton instance
search_service = SearchService()