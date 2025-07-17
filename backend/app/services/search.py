"""Search service using Qdrant vector database."""

import logging
import re
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import select, or_, and_, func, String, cast, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.resume import Resume
from app.services.vector_search import vector_search
from app.services.search_skill_fix import (
    create_skill_search_conditions,
    enhance_search_query_for_skills
)

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
        logger.info(f"\n{'='*60}")
        logger.info(f"SEARCH SERVICE DEBUG - Starting search")
        logger.info(f"Query: '{query}'")
        logger.info(f"Limit: {limit}")
        logger.info(f"Filters: {filters}")
        logger.info(f"{'='*60}\n")
        
        try:
            # First, try vector search with Qdrant
            logger.info("Attempting vector search with Qdrant...")
            vector_results = await vector_search.search_similar(
                query=query,
                limit=limit * 2,  # Get more results to filter
                filters=filters
            )
            logger.info(f"Vector search returned {len(vector_results) if vector_results else 0} results")
            
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
                        
                        # Boost score if exact skill match
                        original_score = vr["score"]
                        if resume.skills:
                            query_lower = query.lower()
                            has_exact_skill = any(
                                query_lower in skill.lower() 
                                for skill in resume.skills if skill
                            )
                            if has_exact_skill:
                                # Boost score for exact skill matches
                                resume_data["_has_exact_skill"] = True
                                boosted_score = min(1.0, original_score * 1.5)
                                search_results.append((resume_data, boosted_score))
                                logger.info(f"Boosted score for {resume.first_name} {resume.last_name} from {original_score} to {boosted_score} (exact skill match)")
                            else:
                                search_results.append((resume_data, original_score))
                        else:
                            search_results.append((resume_data, original_score))
                
                # Sort by score (highest first) and prioritize exact skill matches
                search_results.sort(key=lambda x: (x[0].get("_has_exact_skill", False), x[1]), reverse=True)
                
                # Remove the temporary flag
                for result, _ in search_results:
                    result.pop("_has_exact_skill", None)
                
                return search_results[:limit]
                
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            logger.info("Falling back to keyword search...")
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
        logger.info("\n--- Keyword Search Debug ---")
        logger.info(f"Query: '{query}'")
        
        # Build query
        stmt = select(Resume).where(
            Resume.status == 'active',
            Resume.parse_status == 'completed'
        )
        
        # Add keyword search with enhanced skill matching
        search_terms = query.lower().split()
        logger.info(f"Search terms: {search_terms}")
        
        if search_terms:
            search_conditions = []
            
            # Check if the query might be a skill search
            query_variations = enhance_search_query_for_skills(query)
            logger.info(f"Query variations for skill search: {query_variations}")
            
            for term in search_terms:
                logger.info(f"\nProcessing term: '{term}'")
                term_pattern = f"%{term}%"
                
                # Basic text search conditions
                basic_conditions = [
                    Resume.summary.ilike(term_pattern),
                    Resume.current_title.ilike(term_pattern),
                    Resume.raw_text.ilike(term_pattern)
                ]
                
                # If this term might be a skill, add skill-specific conditions
                if any(term.lower() in var.lower() for var in query_variations):
                    logger.info(f"Term '{term}' identified as potential skill")
                    skill_conditions = create_skill_search_conditions(term, Resume)
                    logger.info(f"Created {len(skill_conditions)} skill-specific conditions")
                    search_conditions.append(or_(*basic_conditions, *skill_conditions))
                else:
                    logger.info(f"Term '{term}' using basic text search only")
                    search_conditions.append(or_(*basic_conditions))
            
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
        
        # Log the final SQL conditions (simplified)
        logger.info(f"\nTotal search conditions: {len(search_conditions) if search_terms else 0}")
        
        # Execute query
        logger.info("Executing database query...")
        result = await db.execute(stmt.limit(limit * 2))  # Get more to ensure we catch all matches
        resumes = result.scalars().all()
        logger.info(f"Query returned {len(resumes)} resumes")
        
        # Debug: Log all found resumes
        if query.lower() == "websphere":
            logger.info("WebSphere search - all found resumes:")
            for r in resumes:
                logger.info(f"  - {r.first_name} {r.last_name}: skills={r.skills}")
        
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
                
                # CRITICAL: Boost score significantly for skill matches
                if resume.skills:
                    # Check for exact skill match (highest priority)
                    if any(term.lower() == skill.lower() for skill in resume.skills if skill):
                        score += 0.5
                        logger.info(f"Exact skill match for '{term}' in {resume.first_name} {resume.last_name}")
                    # Check for partial skill match
                    elif any(term.lower() in skill.lower() for skill in resume.skills if skill):
                        score += 0.3
                        logger.info(f"Partial skill match for '{term}' in {resume.first_name} {resume.last_name}")
            
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
            
            # Check for exact skill match (similar to vector search logic)
            has_exact_skill = False
            if resume.skills:
                query_lower = query.lower()
                has_exact_skill = any(
                    query_lower in skill.lower() 
                    for skill in resume.skills if skill
                )
                if has_exact_skill:
                    # Significant boost for exact skill matches
                    score = min(1.0, score * 1.5)
                    resume_data["_has_exact_skill"] = True
                    logger.info(f"Boosted score for {resume.first_name} {resume.last_name} to {score} (exact skill match in keyword search)")
            
            search_results.append((resume_data, min(score, 1.0)))
        
        # Sort by score AND prioritize exact skill matches (same as vector search)
        search_results.sort(key=lambda x: (x[0].get("_has_exact_skill", False), x[1]), reverse=True)
        
        # Remove the temporary flag
        for result, _ in search_results:
            result.pop("_has_exact_skill", None)
        
        logger.info(f"\nReturning {len(search_results)} results")
        if search_results:
            logger.info("Top 3 results:")
            for i, (resume_data, score) in enumerate(search_results[:3]):
                logger.info(f"  {i+1}. {resume_data['first_name']} {resume_data['last_name']} - Score: {score}")
                logger.info(f"     Title: {resume_data.get('current_title', 'N/A')}")
                logger.info(f"     Skills: {resume_data.get('skills', [])[:5]}...")
        
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
            "websphere": {"category": "tool", "full": "WebSphere Developer"},
            "websphere message broker": {"category": "tool", "full": "WebSphere Message Broker Developer"},
            "wmb": {"category": "tool", "full": "WebSphere Message Broker Developer"},
            "websphere mq": {"category": "tool", "full": "WebSphere MQ Developer"},
            "ibm mq": {"category": "tool", "full": "IBM MQ Developer"},
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
                # Use enhanced skill search for better matching
                if keyword.lower() in ['websphere', 'websphere message broker', 'websphere mq', 'wmb', 'ibm mq']:
                    skill_conditions = create_skill_search_conditions(keyword, Resume)
                    count_stmt = select(func.count(Resume.id)).where(
                        Resume.status == 'active',
                        or_(*skill_conditions)
                    )
                else:
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
        
        # Search for skills in the database that match the query
        if len(suggestions) < 10:
            # Query to find skills that match
            skill_stmt = text("""
                SELECT DISTINCT skill, COUNT(*) as count
                FROM resumes, jsonb_array_elements_text(skills::jsonb) as skill
                WHERE status = 'active' 
                AND LOWER(skill) LIKE LOWER(:query)
                GROUP BY skill
                ORDER BY count DESC
                LIMIT 10
            """)
            
            try:
                logger.info(f"Searching for skills matching '{query}'")
                result = await db.execute(skill_stmt, {"query": f"%{query}%"})
                skill_matches = result.all()
                logger.info(f"Found {len(skill_matches)} matching skills in database")
                
                for skill, count in skill_matches:
                    if skill and skill not in [s["query"] for s in suggestions]:
                        suggestions.append({
                            "query": skill,
                            "count": count,
                            "confidence": 0.85,
                            "category": "skill"
                        })
                        logger.info(f"Added skill suggestion: '{skill}' with {count} matches")
            except Exception as e:
                logger.error(f"Error searching skills: {e}", exc_info=True)
                
                # Fallback: Try a simpler approach
                try:
                    logger.info("Trying fallback skill search method")
                    fallback_stmt = select(Resume.skills).where(
                        Resume.skills.isnot(None),
                        cast(Resume.skills, String).ilike(f'%{query}%')
                    ).limit(20)
                    
                    fallback_result = await db.execute(fallback_stmt)
                    all_skills_lists = fallback_result.scalars().all()
                    
                    # Count occurrences of matching skills
                    skill_counts = {}
                    for skills_list in all_skills_lists:
                        if skills_list:
                            for skill in skills_list:
                                if skill and query.lower() in skill.lower():
                                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
                    
                    # Add top matching skills
                    for skill, count in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                        if skill not in [s["query"] for s in suggestions]:
                            suggestions.append({
                                "query": skill,
                                "count": count,
                                "confidence": 0.8,
                                "category": "skill"
                            })
                            logger.info(f"Added fallback skill: '{skill}' with {count} matches")
                            
                except Exception as fallback_error:
                    logger.error(f"Fallback skill search also failed: {fallback_error}")
        
        # Get job titles from existing resumes that match the full query
        if len(suggestions) < 10:
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
        
        # Debug logging
        logger.info(f"Search suggestions for '{query}': {len(suggestions)} found")
        for s in suggestions[:5]:
            logger.info(f"  - {s['query']} ({s['category']}): {s['count']} matches")
        
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