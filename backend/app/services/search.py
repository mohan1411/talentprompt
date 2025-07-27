"""Search service using Qdrant vector database."""

import logging
import re
from typing import List, Optional, Tuple, Dict, Any, AsyncGenerator
from uuid import UUID

from sqlalchemy import select, or_, and_, func, cast, text
from sqlalchemy.types import String as SQLString
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.resume import Resume
from app.services.vector_search import vector_search
from app.services.search_skill_fix import (
    create_skill_search_conditions,
    enhance_search_query_for_skills
)
from app.services.query_parser import query_parser
from app.services.search_metrics import search_metrics
from app.services.progressive_search import progressive_search
from app.services.gpt4_query_analyzer import gpt4_analyzer

logger = logging.getLogger(__name__)


class SearchService:
    """Service for performing vector similarity search on resumes."""
    
    async def search_resumes(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID,
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
        print(f"\n{'='*60}", flush=True)
        print(f"ENHANCED SEARCH ACTIVE - Starting search", flush=True)
        print(f"Query: '{query}'", flush=True)
        print(f"Limit: {limit}", flush=True)
        print(f"Filters: {filters}", flush=True)
        print(f"User ID: {user_id}", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"SEARCH SERVICE DEBUG - Starting search")
        logger.info(f"Query: '{query}'")
        logger.info(f"Limit: {limit}")
        logger.info(f"Filters: {filters}")
        logger.info(f"{'='*60}\n")
        
        # Start timing for metrics
        import time
        start_time = time.time()
        
        try:
            # First, try vector search with Qdrant
            logger.info("Attempting vector search with Qdrant...")
            vector_results = await vector_search.search_similar(
                query=query,
                user_id=str(user_id),  # SECURITY: Pass user_id to vector search
                limit=limit * 2,  # Get more results to filter
                filters=filters
            )
            print(f"*** VECTOR SEARCH RESULTS: {len(vector_results) if vector_results else 0} results for query '{query}'")
            logger.info(f"Vector search returned {len(vector_results) if vector_results else 0} results")
            
            if vector_results:
                # Get resume IDs from vector search
                resume_ids = [r["resume_id"] for r in vector_results]
                logger.info(f"Vector search returned IDs: {resume_ids[:5]}...")  # Log first 5
                
                # Fetch full resume data from PostgreSQL - CRITICAL: Filter by user_id
                stmt = select(Resume).where(
                    Resume.id.in_(resume_ids),
                    Resume.user_id == user_id  # SECURITY: Only show user's own resumes
                )
                result = await db.execute(stmt)
                resumes = {str(r.id): r for r in result.scalars().all()}
                logger.info(f"Found {len(resumes)} resumes in PostgreSQL matching vector IDs for user {user_id}")
                
                # Combine results with scores
                search_results = []
                for vr in vector_results:
                    resume_id = str(vr["resume_id"])  # Ensure it's a string
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
                        
                        # Enhanced skill matching with query parser
                        original_score = vr["score"]
                        
                        # Parse the query to extract required skills
                        parsed_query = query_parser.parse_query(query)
                        required_skills = parsed_query["skills"]
                        primary_skill = parsed_query.get("primary_skill")
                        print(f"*** PARSED QUERY for '{query}': required_skills={required_skills}, primary={primary_skill}")
                        
                        if resume.skills and required_skills:
                            # Calculate skill match score with primary skill weighting
                            resume_skills_lower = [skill.lower() for skill in resume.skills if skill]
                            matched_skills = []
                            matched_primary = False
                            total_required = len(required_skills)
                            
                            # Check which skills match
                            for required_skill in required_skills:
                                # Check for exact match or partial match
                                if any(required_skill in skill for skill in resume_skills_lower):
                                    matched_skills.append(required_skill)
                                    if required_skill == primary_skill:
                                        matched_primary = True
                            
                            # Calculate weighted score
                            # Primary skill is worth 60% of the score if it's the only required skill
                            # or 50% if there are multiple required skills
                            if total_required == 1:
                                skill_match_ratio = 1.0 if matched_primary else 0.0
                            else:
                                primary_weight = 0.5 if primary_skill else 0
                                secondary_weight = (1.0 - primary_weight) / (total_required - 1) if total_required > 1 else 0
                                
                                weighted_score = 0.0
                                if matched_primary:
                                    weighted_score += primary_weight
                                
                                # Add score for secondary skills
                                secondary_matches = len([s for s in matched_skills if s != primary_skill])
                                if total_required > 1:
                                    weighted_score += secondary_matches * secondary_weight
                                
                                skill_match_ratio = weighted_score
                            
                            # Store match details
                            resume_data["_matched_skills"] = matched_skills
                            resume_data["_has_primary"] = matched_primary
                            resume_data["_skill_match_ratio"] = skill_match_ratio
                            
                            # 5-tier system based on skill matches
                            if skill_match_ratio == 1.0:
                                # Tier 1: All skills match (100%)
                                hybrid_score = min(1.0, original_score * 1.5)
                                resume_data["_skill_tier"] = 1
                                tier_name = "TIER 1 PERFECT"
                                print(f"*** {tier_name}: {resume.first_name} {resume.last_name} has ALL skills - boosted to {hybrid_score:.3f}")
                            elif matched_primary and skill_match_ratio >= 0.75:
                                # Tier 2: Has primary skill + most secondary (75%+)
                                hybrid_score = original_score * 0.8
                                resume_data["_skill_tier"] = 2
                                tier_name = "TIER 2 PRIMARY+"
                                print(f"*** {tier_name}: {resume.first_name} {resume.last_name} has primary + secondary - score: {hybrid_score:.3f}")
                            elif matched_primary and skill_match_ratio >= 0.5:
                                # Tier 3: Has primary skill only (50-74%)
                                hybrid_score = original_score * 0.5
                                resume_data["_skill_tier"] = 3
                                tier_name = "TIER 3 PRIMARY"
                                print(f"*** {tier_name}: {resume.first_name} {resume.last_name} has primary skill only - score: {hybrid_score:.3f}")
                            elif not matched_primary and len(matched_skills) > 0:
                                # Tier 4: Has secondary skills only
                                hybrid_score = original_score * 0.2
                                resume_data["_skill_tier"] = 4
                                tier_name = "TIER 4 SECONDARY"
                                print(f"*** {tier_name}: {resume.first_name} {resume.last_name} has secondary skills only - score: {hybrid_score:.3f}")
                            else:
                                # Tier 5: No relevant skills (0%)
                                hybrid_score = original_score * 0.05
                                resume_data["_skill_tier"] = 5
                                tier_name = "TIER 5 NO MATCH"
                                print(f"*** {tier_name}: {resume.first_name} {resume.last_name} has NO required skills - score: {hybrid_score:.3f}")
                            
                            search_results.append((resume_data, hybrid_score))
                            logger.info(f"{tier_name} for {resume.first_name} {resume.last_name}: matched={matched_skills}, primary={matched_primary}, score={hybrid_score:.3f}")
                        else:
                            # No skills to match or no skills in resume
                            search_results.append((resume_data, original_score))
                
                # Sort with multiple criteria: first by skill tier, then by score
                # This ensures candidates with all skills always rank above those with partial matches
                def sort_key(item):
                    resume_data, score = item
                    # Lower tier number = better match (1=perfect, 2=primary+, 3=primary, 4=secondary, 5=none)
                    skill_tier = resume_data.get("_skill_tier", 999)  # Default to worst tier
                    # Return tuple: (tier, -score) for ascending tier order, descending score order
                    return (skill_tier, -score)
                
                search_results.sort(key=sort_key)
                
                # Clean up internal flags but keep useful match details
                for result, _ in search_results:
                    # Convert internal data to public fields
                    result["skill_tier"] = result.pop("_skill_tier", None)
                    result["matched_skills"] = result.pop("_matched_skills", [])
                    result["has_primary_skill"] = result.pop("_has_primary", False)
                    result["skill_match_score"] = result.pop("_skill_match_ratio", 0)
                    
                    # Remove any remaining internal flags
                    result.pop("_all_skills_match", None)
                
                # Additional filtering: If this is a specific skill search (e.g., "Python Developer")
                # and we have enough results with all skills, filter out partial matches
                if required_skills and len(search_results) > limit:
                    # Count how many have all required skills
                    full_matches = sum(1 for r, s in search_results if s > 0.65)  # Assume >0.65 means good match
                    if full_matches >= limit:
                        # Filter to only include high-scoring results
                        logger.info(f"Filtering to high-quality matches only (found {full_matches} good matches)")
                        search_results = [(r, s) for r, s in search_results if s > 0.5]
                
                # If we have results, log metrics and return
                if search_results:
                    final_results = search_results[:limit]
                    
                    # Log search metrics
                    elapsed_time = time.time() - start_time
                    metrics = search_metrics.log_search(
                        query=query,
                        results=final_results,
                        search_time=elapsed_time,
                        search_type="vector"
                    )
                    
                    return final_results
                else:
                    logger.warning("Vector search returned IDs but no matching resumes found in PostgreSQL")
                    # Fall through to keyword search
                
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            logger.info("Falling back to keyword search...")
            # Fall back to keyword search
        
        # Fallback: Keyword-based search using PostgreSQL
        keyword_results = await self._keyword_search(db, query, user_id, limit, filters)
        
        # Log metrics for keyword search
        elapsed_time = time.time() - start_time
        metrics = search_metrics.log_search(
            query=query,
            results=keyword_results,
            search_time=elapsed_time,
            search_type="keyword"
        )
        
        return keyword_results
    
    async def _keyword_search(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID,
        limit: int = 10,
        filters: Optional[dict] = None
    ) -> List[Tuple[dict, float]]:
        """Fallback keyword search using PostgreSQL."""
        logger.info("\n--- Keyword Search Debug ---")
        logger.info(f"Query: '{query}'")
        
        # Build query - CRITICAL: Filter by user_id
        stmt = select(Resume).where(
            Resume.status == 'active',
            Resume.parse_status == 'completed',
            Resume.user_id == user_id  # SECURITY: Only show user's own resumes
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
                        func.cast(Resume.skills, SQLString).ilike(f'%"{skill}"%')
                    )
        
        # Log the final SQL conditions (simplified)
        logger.info(f"\nTotal search conditions: {len(search_conditions) if search_terms else 0}")
        
        # Execute query - for skill searches, get more results to ensure we don't miss exact matches
        logger.info("Executing database query...")
        # If searching for a potential skill, get more results to ensure exact matches aren't missed
        is_skill_search = any(term.lower() in enhance_search_query_for_skills(query) for term in search_terms)
        fetch_limit = limit * 5 if is_skill_search else limit * 2
        logger.info(f"Fetching up to {fetch_limit} results (skill search: {is_skill_search})")
        
        result = await db.execute(stmt.limit(fetch_limit))
        resumes = result.scalars().all()
        logger.info(f"Query returned {len(resumes)} resumes")
        
        # Debug: Log all found resumes
        if query.lower() == "websphere":
            logger.info("WebSphere search - all found resumes:")
            for r in resumes:
                logger.info(f"  - {r.first_name} {r.last_name}: skills={r.skills}")
        
        # CRITICAL FIX: Also explicitly search for exact skill matches to ensure they're included
        if is_skill_search and len(resumes) < fetch_limit:
            logger.info("Adding explicit exact skill match search...")
            # Search for resumes with exact skill match that might have been missed
            exact_skill_stmt = select(Resume).where(
                Resume.status == 'active',
                Resume.parse_status == 'completed',
                Resume.user_id == user_id  # SECURITY: Only show user's own resumes
            )
            
            # Add exact skill conditions
            skill_conditions = []
            for term in search_terms:
                for variation in enhance_search_query_for_skills(term):
                    skill_conditions.append(
                        cast(Resume.skills, SQLString).ilike(f'%"{variation}"%')
                    )
            
            if skill_conditions:
                exact_skill_stmt = exact_skill_stmt.where(or_(*skill_conditions))
                exact_result = await db.execute(exact_skill_stmt.limit(50))
                exact_matches = exact_result.scalars().all()
                
                # Add any missing exact matches
                existing_ids = {r.id for r in resumes}
                for resume in exact_matches:
                    if resume.id not in existing_ids:
                        resumes.append(resume)
                        logger.info(f"Added exact skill match: {resume.first_name} {resume.last_name}")
        
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
            
            # Enhanced skill matching for keyword search
            parsed_query = query_parser.parse_query(query)
            required_skills = parsed_query["skills"]
            
            if resume.skills and required_skills:
                # Calculate skill match score
                resume_skills_lower = [skill.lower() for skill in resume.skills if skill]
                matched_skills = 0
                total_required = len(required_skills)
                
                for required_skill in required_skills:
                    # Check for exact match or partial match
                    if any(required_skill in skill for skill in resume_skills_lower):
                        matched_skills += 1
                
                skill_match_ratio = matched_skills / total_required if total_required > 0 else 0
                
                # Apply skill-based scoring with aggressive penalties
                if skill_match_ratio == 1.0:
                    # All skills match - significant boost
                    score = min(1.0, score * 1.5)
                    resume_data["_all_skills_match"] = True
                    logger.info(f"All skills match for {resume.first_name} {resume.last_name}, boosted score: {score:.3f}")
                elif skill_match_ratio >= 0.5:
                    # Partial match - apply significant penalty
                    penalty_factor = 0.2 + (skill_match_ratio * 0.4)  # 0.4 for 50%, 0.6 for 75%
                    score = score * penalty_factor
                    logger.info(f"Partial skill match ({matched_skills}/{total_required}) for {resume.first_name} {resume.last_name}, penalty={penalty_factor:.2f}, score: {score:.3f}")
                else:
                    # Poor skill match - severe penalty
                    score = score * 0.3
                    logger.info(f"Poor skill match ({matched_skills}/{total_required}) for {resume.first_name} {resume.last_name} in keyword search, heavily penalized: {score:.3f}")
            
            search_results.append((resume_data, min(score, 1.0)))
        
        # Sort by score AND prioritize all skill matches (same as vector search)
        search_results.sort(key=lambda x: (x[0].get("_all_skills_match", False), x[1]), reverse=True)
        
        # Remove the temporary flag
        for result, _ in search_results:
            result.pop("_all_skills_match", None)
        
        # Limit results after sorting to ensure best matches are included
        search_results = search_results[:limit]
        
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
        user_id: UUID,
        limit: int = 5
    ) -> List[Tuple[dict, float]]:
        """Find similar resumes to a given resume."""
        # Get the resume - CRITICAL: Ensure it belongs to the user
        stmt = select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == user_id  # SECURITY: Only access user's own resumes
        )
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
        
        # Search for similar resumes - pass user_id
        results = await self.search_resumes(db, query, user_id, limit + 1)
        
        # Filter out the original resume
        return [(r, s) for r, s in results if r["id"] != str(resume_id)][:limit]
    
    async def get_search_suggestions(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID
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
                Resume.user_id == user_id,  # SECURITY: Only count user's own resumes
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
                            func.cast(Resume.skills, SQLString).ilike(f'%"{found_tech}"%'),
                            func.cast(Resume.skills, SQLString).ilike(f'%"{found_tech.title()}"%'),
                            func.cast(Resume.skills, SQLString).ilike(f'%"{found_tech.upper()}"%')
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
                    Resume.user_id == user_id,  # SECURITY: Only count user's own resumes
                    or_(
                        Resume.current_title.ilike(f"%{found_tech}%"),
                        Resume.summary.ilike(f"%{found_tech}%"),
                        func.cast(Resume.skills, SQLString).ilike(f'%"{found_tech}"%'),
                        func.cast(Resume.skills, SQLString).ilike(f'%"{found_tech.title()}"%')
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
                        Resume.user_id == user_id,  # SECURITY: Only count user's own resumes
                        or_(*skill_conditions)
                    )
                else:
                    count_stmt = select(func.count(Resume.id)).where(
                        Resume.status == 'active',
                        Resume.user_id == user_id,  # SECURITY: Only count user's own resumes
                        or_(
                            Resume.summary.ilike(f"%{keyword}%"),
                            Resume.current_title.ilike(f"%{keyword}%"),
                            func.cast(Resume.skills, SQLString).ilike(f'%"{keyword}"%')
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
                AND user_id = :user_id
                AND LOWER(skill) LIKE LOWER(:query)
                GROUP BY skill
                ORDER BY count DESC
                LIMIT 10
            """)
            
            try:
                logger.info(f"Searching for skills matching '{query}'")
                result = await db.execute(skill_stmt, {"query": f"%{query}%", "user_id": user_id})
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
                        Resume.user_id == user_id,  # SECURITY: Only search user's own resumes
                        cast(Resume.skills, SQLString).ilike(f'%{query}%')
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
                Resume.status == 'active',
                Resume.user_id == user_id  # SECURITY: Only show user's own titles
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
        user_id: UUID,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get popular skills and technologies from resumes."""
        # Get all resumes with skills - CRITICAL: Filter by user_id
        stmt = select(Resume.skills).where(
            Resume.skills.isnot(None),
            Resume.status == 'active',
            Resume.user_id == user_id  # SECURITY: Only show user's own tags
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
    
    async def search_resumes_progressive(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID,
        limit: int = 10,
        filters: Optional[dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Progressive search that yields results in stages.
        
        This is the new enhanced search method that provides:
        1. Instant results from cache/keywords
        2. Enhanced results with vector search
        3. Intelligent results with GPT-4.1-mini analysis
        
        Yields:
            Dictionary with stage info and results
        """
        # Use the progressive search engine
        async for stage_result in progressive_search.search_progressive(
            db=db,
            query=query,
            user_id=user_id,
            limit=limit,
            filters=filters
        ):
            yield stage_result
    
    async def analyze_query_advanced(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze query using GPT-4.1-mini for advanced understanding.
        
        Args:
            query: Search query
            context: Optional context (search history, preferences)
            
        Returns:
            Advanced query analysis
        """
        return await gpt4_analyzer.analyze_query(query, context)
    
    async def search_resumes_progressive(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID,
        limit: int = 10,
        filters: Optional[dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Progressive search that yields results in stages.
        
        Args:
            db: Database session
            query: Search query
            user_id: User ID
            limit: Maximum number of results
            filters: Optional filters
            
        Yields:
            Stage results with timing and metadata
        """
        async for stage_result in progressive_search.search_progressive(
            db=db,
            query=query,
            user_id=user_id,
            limit=limit,
            filters=filters
        ):
            yield stage_result


# Create singleton instance
search_service = SearchService()