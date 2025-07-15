"""Search service using Qdrant vector database."""

import logging
import re
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import select, or_, and_, func, String
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
                    # Use PostgreSQL JSON operators
                    # Cast JSON to text and use ILIKE for case-insensitive search
                    stmt = stmt.where(
                        func.cast(Resume.skills, String).ilike(f'%"{skill}"%')
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
    
    async def get_search_suggestions(
        self,
        db: AsyncSession,
        query: str
    ) -> List[Dict[str, Any]]:
        """Get search suggestions based on partial query."""
        suggestions = []
        
        if len(query) < 2:
            return suggestions
        
        query_lower = query.lower()
        query_words = query_lower.split()
        
        # Common technology suggestions with multi-word support
        tech_keywords = {
            "python": {"category": "language", "full": "Python Developer"},
            "java": {"category": "language", "full": "Java Developer"},
            "javascript": {"category": "language", "full": "JavaScript Developer"},
            "react": {"category": "framework", "full": "React Developer"},
            "angular": {"category": "framework", "full": "Angular Developer"},
            "vue": {"category": "framework", "full": "Vue.js Developer"},
            "node": {"category": "runtime", "full": "Node.js Developer"},
            "aws": {"category": "cloud", "full": "AWS Cloud Engineer"},
            "azure": {"category": "cloud", "full": "Azure Cloud Engineer"},
            "docker": {"category": "tool", "full": "Docker/DevOps Engineer"},
            "kubernetes": {"category": "tool", "full": "Kubernetes Engineer"},
            "machine learning": {"category": "field", "full": "Machine Learning Engineer"},
            "data science": {"category": "field", "full": "Data Scientist"},
            "frontend": {"category": "role", "full": "Frontend Developer"},
            "backend": {"category": "role", "full": "Backend Developer"},
            "fullstack": {"category": "role", "full": "Full Stack Developer"},
            "devops": {"category": "role", "full": "DevOps Engineer"},
            "senior": {"category": "level", "full": "Senior Developer"},
            "junior": {"category": "level", "full": "Junior Developer"},
            "lead": {"category": "level", "full": "Tech Lead"},
        }
        
        # Additional multi-word combinations
        level_modifiers = ["senior", "junior", "lead", "principal", "staff"]
        role_keywords = ["developer", "engineer", "architect", "manager", "analyst"]
        
        # Build contextual suggestions based on query words
        found_level = None
        found_tech = None
        found_role = None
        
        for word in query_words:
            if word in level_modifiers:
                found_level = word
            elif word in tech_keywords:
                found_tech = word
            elif word in role_keywords:
                found_role = word
        
        # Generate contextual suggestions
        if found_level and found_tech:
            # e.g., "senior python" -> "Senior Python Developer"
            tech_info = tech_keywords.get(found_tech, {})
            suggested_title = f"{found_level.title()} {tech_info.get('full', found_tech.title() + ' Developer')}"
            
            # Count actual resumes matching this combination
            # Check for both words appearing together (with possible words in between)
            count_stmt = select(func.count(Resume.id)).where(
                Resume.status == 'active',
                or_(
                    # Check for level AND tech in title/summary
                    and_(
                        Resume.current_title.ilike(f"%{found_level}%"),
                        Resume.current_title.ilike(f"%{found_tech}%")
                    ),
                    and_(
                        Resume.summary.ilike(f"%{found_level}%"),
                        Resume.summary.ilike(f"%{found_tech}%")
                    ),
                    # Also check for exact phrase
                    Resume.current_title.ilike(f"%{found_level} {found_tech}%"),
                    Resume.summary.ilike(f"%{found_level} {found_tech}%"),
                    # Check skills JSON for the technology (case-insensitive)
                    and_(
                        or_(
                            Resume.current_title.ilike(f"%{found_level}%"),
                            Resume.summary.ilike(f"%{found_level}%")
                        ),
                        or_(
                            func.cast(Resume.skills, String).ilike(f'%"{found_tech}"%'),
                            func.cast(Resume.skills, String).ilike(f'%"{found_tech.title()}"%'),
                            func.cast(Resume.skills, String).ilike(f'%"{found_tech.upper()}"%')
                        )
                    )
                )
            )
            count_result = await db.execute(count_stmt)
            actual_count = count_result.scalar() or 0
            
            # If no exact matches found, try counting just the technology
            if actual_count == 0:
                tech_count_stmt = select(func.count(Resume.id)).where(
                    Resume.status == 'active',
                    or_(
                        Resume.current_title.ilike(f"%{found_tech}%"),
                        Resume.summary.ilike(f"%{found_tech}%"),
                        func.cast(Resume.skills, String).ilike(f'%"{found_tech}"%'),
                        func.cast(Resume.skills, String).ilike(f'%"{found_tech.title()}"%')
                    )
                )
                tech_count_result = await db.execute(tech_count_stmt)
                tech_count = tech_count_result.scalar() or 0
                
                # Show tech count as a hint
                if tech_count > 0:
                    actual_count = tech_count
                    suggested_title = f"{suggested_title} ({tech_count} {found_tech.title()} developers)"
            
            suggestions.append({
                "query": suggested_title,
                "count": actual_count,
                "confidence": 0.95,
                "category": "combined"
            })
        
        # Find matching single keywords
        for keyword, info in tech_keywords.items():
            if any(keyword.startswith(word) or word in keyword for word in query_words):
                # Count actual resumes with this keyword
                count_stmt = select(func.count(Resume.id)).where(
                    Resume.status == 'active',
                    or_(
                        Resume.summary.ilike(f"%{keyword}%"),
                        Resume.current_title.ilike(f"%{keyword}%"),
                        func.cast(Resume.skills, String).ilike(f'%"{keyword}"%')
                    )
                )
                count_result = await db.execute(count_stmt)
                actual_count = count_result.scalar() or 0
                
                if actual_count > 0:
                    suggestions.append({
                        "query": info["full"],
                        "count": actual_count,
                        "confidence": 0.9 if keyword == query_lower else 0.7,
                        "category": info["category"]
                    })
        
        # Get job titles from existing resumes that match the full query
        if len(suggestions) < 5:
            # First try exact phrase match
            stmt = select(Resume.current_title, func.count(Resume.id)).where(
                Resume.current_title.ilike(f"%{query}%"),
                Resume.status == 'active'
            ).group_by(Resume.current_title).limit(5)
            
            result = await db.execute(stmt)
            title_counts = result.all()
            
            for title, count in title_counts:
                if title and title not in [s["query"] for s in suggestions]:
                    suggestions.append({
                        "query": title,
                        "count": count,
                        "confidence": 0.8,
                        "category": "title"
                    })
        
        # Sort by confidence and count
        suggestions.sort(key=lambda x: (x["confidence"], x["count"]), reverse=True)
        
        return suggestions[:10]  # Limit to 10 suggestions
    
    async def get_popular_tags(
        self,
        db: AsyncSession,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get popular skills and technologies from resumes."""
        # Get all resumes with skills
        stmt = select(Resume.skills).where(
            Resume.skills.isnot(None),
            Resume.status == 'active'
        )
        
        result = await db.execute(stmt)
        all_skills = result.scalars().all()
        
        # Count skill occurrences
        skill_counts = {}
        for skills_list in all_skills:
            if skills_list:
                for skill in skills_list:
                    skill_lower = skill.lower()
                    if skill_lower in skill_counts:
                        skill_counts[skill_lower]["count"] += 1
                    else:
                        skill_counts[skill_lower] = {
                            "name": skill,
                            "count": 1,
                            "category": self._categorize_skill(skill_lower)
                        }
        
        # Sort by count and return top skills
        sorted_skills = sorted(
            skill_counts.values(),
            key=lambda x: x["count"],
            reverse=True
        )
        
        return sorted_skills[:limit]
    
    def _categorize_skill(self, skill: str) -> str:
        """Categorize a skill based on common patterns."""
        skill_lower = skill.lower()
        
        # Programming languages
        languages = ["python", "java", "javascript", "typescript", "c++", "c#", 
                    "ruby", "go", "rust", "swift", "kotlin", "php", "r", "scala"]
        if any(lang in skill_lower for lang in languages):
            return "language"
        
        # Frameworks
        frameworks = ["react", "angular", "vue", "django", "flask", "spring", 
                     "express", "rails", "laravel", ".net", "tensorflow", "pytorch"]
        if any(fw in skill_lower for fw in frameworks):
            return "framework"
        
        # Tools & Technologies
        tools = ["docker", "kubernetes", "jenkins", "git", "terraform", "ansible",
                "elasticsearch", "redis", "mongodb", "postgresql", "mysql"]
        if any(tool in skill_lower for tool in tools):
            return "tool"
        
        # Cloud platforms
        cloud = ["aws", "azure", "gcp", "google cloud", "cloud"]
        if any(c in skill_lower for c in cloud):
            return "cloud"
        
        # Default
        return "skill"


# Create singleton instance
search_service = SearchService()