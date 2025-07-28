"""Progressive search engine that delivers results in stages for optimal UX."""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
from uuid import UUID
from datetime import datetime, timezone
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, cast
from sqlalchemy.types import String as SQLString

from app.models.resume import Resume
from app.services.vector_search import vector_search
from app.services.query_parser import query_parser
from app.services.hybrid_search import hybrid_search
from app.services.gpt4_query_analyzer import gpt4_analyzer
from app.services.candidate_analytics import candidate_analytics_service
from app.core.redis import get_redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProgressiveSearchEngine:
    """
    Implements a multi-stage progressive search that delivers results incrementally:
    1. Instant Results: Cache hits and basic keyword matches (<50ms)
    2. Enhanced Results: Vector search with skill matching (<200ms)
    3. Intelligent Results: Deep analysis with explanations (<500ms)
    """
    
    def __init__(self):
        self.cache_ttl = 3600  # 1 hour cache
        self.redis_client = None
        
    async def _get_redis(self):
        """Get Redis client lazily."""
        if not self.redis_client:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    async def search_progressive(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID,
        limit: int = 10,
        filters: Optional[dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Perform progressive search that yields results in stages.
        
        Yields:
            Dictionary with stage info and results
        """
        start_time = time.time()
        search_id = f"search_{user_id}_{int(time.time() * 1000)}"
        
        # Parse query once for all stages
        parsed_query = query_parser.parse_query(query)
        required_skills = parsed_query["skills"]
        primary_skill = parsed_query.get("primary_skill")
        
        logger.info(f"Progressive search started: '{query}' for user {user_id}")
        
        # Stage 1: Instant Results (Cache + Basic Keyword)
        stage1_results = await self._stage1_instant_results(
            db, query, user_id, limit, filters, parsed_query
        )
        
        yield {
            "stage": "instant",
            "stage_number": 1,
            "total_stages": 3,
            "search_id": search_id,
            "query": query,
            "parsed_query": parsed_query,
            "results": stage1_results,
            "count": len(stage1_results),
            "timing_ms": int((time.time() - start_time) * 1000),
            "is_final": False
        }
        
        # Stage 2: Enhanced Results (Vector Search + Skill Matching)
        stage2_results = await self._stage2_enhanced_results(
            db, query, user_id, limit * 2, filters, parsed_query, stage1_results
        )
        
        # Merge and deduplicate results
        merged_results = self._merge_results(stage1_results, stage2_results, limit)
        
        yield {
            "stage": "enhanced", 
            "stage_number": 2,
            "total_stages": 3,
            "search_id": search_id,
            "query": query,
            "parsed_query": parsed_query,
            "results": merged_results,
            "count": len(merged_results),
            "timing_ms": int((time.time() - start_time) * 1000),
            "is_final": False
        }
        
        # Stage 3: Intelligent Results (Deep Analysis + Explanations)
        final_results = await self._stage3_intelligent_results(
            db, merged_results, query, parsed_query, user_id
        )
        
        # Cache the final results
        await self._cache_results(query, user_id, final_results)
        
        yield {
            "stage": "intelligent",
            "stage_number": 3,
            "total_stages": 3,
            "search_id": search_id,
            "query": query,
            "parsed_query": parsed_query,
            "results": final_results[:limit],
            "count": len(final_results[:limit]),
            "timing_ms": int((time.time() - start_time) * 1000),
            "is_final": True,
            "search_quality_score": self._calculate_quality_score(final_results[:limit], parsed_query)
        }
    
    async def _stage1_instant_results(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID,
        limit: int,
        filters: Optional[dict],
        parsed_query: Dict[str, Any]
    ) -> List[Tuple[dict, float]]:
        """
        Stage 1: Return instant results from cache or basic keyword search.
        Target: <50ms
        """
        # Try cache first
        cached = await self._get_cached_results(query, user_id)
        if cached:
            logger.info(f"Stage 1: Cache hit for '{query}'")
            return cached[:limit]
        
        # Quick keyword search for exact skill matches
        if parsed_query["skills"]:
            results = await self._quick_skill_search(db, user_id, parsed_query["skills"], limit)
            if results:
                logger.info(f"Stage 1: Found {len(results)} quick matches")
                return results
        
        # Fallback: Basic text search on current_title
        return await self._basic_keyword_search(db, query, user_id, limit)
    
    async def _stage2_enhanced_results(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID,
        limit: int,
        filters: Optional[dict],
        parsed_query: Dict[str, Any],
        stage1_results: List[Tuple[dict, float]]
    ) -> List[Tuple[dict, float]]:
        """
        Stage 2: Enhanced results with hybrid search (BM25 + vector).
        Target: <200ms
        """
        # Get query analysis to determine query type
        try:
            # Try to get from parsed_query if already analyzed
            query_type = parsed_query.get("query_type", "technical")
        except:
            query_type = "technical"
        
        # Adjust hybrid search weights based on query type
        hybrid_search.adjust_weights(query_type)
        
        # Perform hybrid search
        hybrid_results = await hybrid_search.search(
            db=db,
            query=query,
            user_id=str(user_id),
            limit=limit,
            filters=filters,
            use_synonyms=True
        )
        
        if not hybrid_results:
            return []
        
        # Apply skill-based scoring enhancements
        enhanced_results = []
        for resume_data, hybrid_score in hybrid_results:
            # Add additional skill analysis
            skill_analysis = self._analyze_skill_match(resume_data, parsed_query)
            resume_data["skill_analysis"] = skill_analysis
            
            # Add candidate analytics (availability, learning velocity, etc.)
            resume_data["availability_score"] = candidate_analytics_service.calculate_availability_score(resume_data)
            resume_data["learning_velocity"] = candidate_analytics_service.calculate_learning_velocity(resume_data)
            resume_data["career_trajectory"] = candidate_analytics_service.analyze_career_trajectory(resume_data)
            
            # Calculate final enhanced score
            skill_boost = 0.0
            if skill_analysis["matched"]:
                match_ratio = len(skill_analysis["matched"]) / len(parsed_query.get("skills", []) or [1])
                skill_boost = match_ratio * 0.2  # Up to 20% boost for skill matches
            
            enhanced_score = min(1.0, hybrid_score + skill_boost)
            
            # Add hybrid search metadata
            resume_data["search_metadata"] = {
                "hybrid_score": hybrid_score,
                "keyword_score": resume_data.get("keyword_score", 0),
                "vector_score": resume_data.get("vector_score", 0),
                "skill_boost": skill_boost
            }
            
            enhanced_results.append((resume_data, enhanced_score))
        
        # Sort by enhanced score
        enhanced_results.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Stage 2: Hybrid search found {len(enhanced_results)} results with query type '{query_type}'")
        
        return enhanced_results
    
    async def _stage3_intelligent_results(
        self,
        db: AsyncSession,
        results: List[Tuple[dict, float]],
        query: str,
        parsed_query: Dict[str, Any],
        user_id: UUID
    ) -> List[Tuple[dict, float]]:
        """
        Stage 3: Add intelligent analysis and explanations using GPT-4.1-mini.
        Target: <500ms
        """
        # First add basic analysis
        for resume_data, score in results:
            # Add skill match details
            skill_analysis = self._analyze_skill_match(resume_data, parsed_query)
            resume_data["skill_analysis"] = skill_analysis
        
        # Then enhance with GPT-4.1-mini if available
        try:
            from app.services.result_enhancer import result_enhancer
            
            # Enhance top results with AI insights
            enhanced_results = await result_enhancer.enhance_results(
                results=results,
                query=query,
                parsed_query=parsed_query,
                limit=5  # Enhance top 5 for speed
            )
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error in AI enhancement: {e}")
            # Fallback to basic explanations
            for resume_data, score in results:
                explanation = self._generate_basic_explanation(resume_data, parsed_query, score)
                resume_data["match_explanation"] = explanation
            
            return results
    
    def _calculate_enhanced_score(
        self,
        resume_data: dict,
        vector_score: float,
        parsed_query: Dict[str, Any]
    ) -> float:
        """Calculate enhanced score with skill matching."""
        required_skills = parsed_query["skills"]
        primary_skill = parsed_query.get("primary_skill")
        
        if not required_skills or not resume_data.get("skills"):
            return vector_score
        
        # Calculate skill match
        resume_skills_lower = [s.lower() for s in resume_data["skills"]]
        matched_skills = []
        matched_primary = False
        
        for skill in required_skills:
            if any(skill in rs for rs in resume_skills_lower):
                matched_skills.append(skill)
                if skill == primary_skill:
                    matched_primary = True
        
        # Calculate weighted score
        if len(required_skills) == 1:
            skill_match_ratio = 1.0 if matched_primary else 0.0
        else:
            primary_weight = 0.5 if primary_skill else 0
            secondary_weight = (1.0 - primary_weight) / (len(required_skills) - 1) if len(required_skills) > 1 else 0
            
            weighted_score = 0.0
            if matched_primary:
                weighted_score += primary_weight
            
            secondary_matches = len([s for s in matched_skills if s != primary_skill])
            if len(required_skills) > 1:
                weighted_score += secondary_matches * secondary_weight
            
            skill_match_ratio = weighted_score
        
        # Apply tier-based scoring
        if skill_match_ratio == 1.0:
            return min(1.0, vector_score * 1.5)
        elif matched_primary and skill_match_ratio >= 0.75:
            return vector_score * 0.8
        elif matched_primary and skill_match_ratio >= 0.5:
            return vector_score * 0.5
        elif not matched_primary and len(matched_skills) > 0:
            return vector_score * 0.2
        else:
            return vector_score * 0.05
    
    def _resume_to_dict(self, resume: Resume) -> dict:
        """Convert resume model to dictionary."""
        return {
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
    
    def _merge_results(
        self,
        stage1: List[Tuple[dict, float]],
        stage2: List[Tuple[dict, float]],
        limit: int
    ) -> List[Tuple[dict, float]]:
        """Merge and deduplicate results from multiple stages."""
        seen_ids = set()
        merged = []
        
        # Add all results, deduplicating by ID
        for results in [stage1, stage2]:
            for resume_data, score in results:
                resume_id = resume_data["id"]
                if resume_id not in seen_ids:
                    seen_ids.add(resume_id)
                    merged.append((resume_data, score))
        
        # Sort by score and return top results
        merged.sort(key=lambda x: x[1], reverse=True)
        return merged[:limit]
    
    def _generate_basic_explanation(
        self,
        resume_data: dict,
        parsed_query: Dict[str, Any],
        score: float
    ) -> str:
        """Generate basic match explanation."""
        explanations = []
        
        # Check skill matches
        if parsed_query["skills"] and resume_data.get("skills"):
            resume_skills_lower = [s.lower() for s in resume_data["skills"]]
            matched_skills = []
            
            for skill in parsed_query["skills"]:
                if any(skill in rs for rs in resume_skills_lower):
                    matched_skills.append(skill)
            
            if matched_skills:
                explanations.append(f"Has {len(matched_skills)}/{len(parsed_query['skills'])} required skills: {', '.join(matched_skills)}")
        
        # Check title match
        if resume_data.get("current_title") and any(
            word in resume_data["current_title"].lower() 
            for word in parsed_query["original_query"].lower().split()
        ):
            explanations.append(f"Current role: {resume_data['current_title']}")
        
        # Check experience
        if resume_data.get("years_experience"):
            explanations.append(f"{resume_data['years_experience']} years of experience")
        
        # Add score indicator
        if score > 0.8:
            explanations.insert(0, "Excellent match")
        elif score > 0.6:
            explanations.insert(0, "Strong match")
        elif score > 0.4:
            explanations.insert(0, "Good match")
        else:
            explanations.insert(0, "Partial match")
        
        return " • ".join(explanations) if explanations else "Relevant candidate"
    
    def _analyze_skill_match(
        self,
        resume_data: dict,
        parsed_query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze skill match details."""
        required_skills = parsed_query["skills"]
        if not required_skills or not resume_data.get("skills"):
            return {"matched": [], "missing": required_skills or [], "additional": []}
        
        resume_skills_lower = [s.lower() for s in resume_data["skills"]]
        matched = []
        missing = []
        
        for skill in required_skills:
            if any(skill in rs for rs in resume_skills_lower):
                matched.append(skill)
            else:
                missing.append(skill)
        
        # Find additional relevant skills
        additional = []
        skill_categories = {
            "python": ["django", "flask", "pandas", "numpy"],
            "javascript": ["react", "angular", "vue", "node.js"],
            "aws": ["ec2", "s3", "lambda", "dynamodb"],
        }
        
        for category, related in skill_categories.items():
            if category in matched:
                for related_skill in related:
                    if any(related_skill in rs for rs in resume_skills_lower):
                        if related_skill not in matched:
                            additional.append(related_skill)
        
        return {
            "matched": matched,
            "missing": missing,
            "additional": additional[:5],  # Limit to top 5
            "match_percentage": len(matched) / len(required_skills) * 100 if required_skills else 0
        }
    
    def _calculate_quality_score(
        self,
        results: List[Tuple[dict, float]],
        parsed_query: Dict[str, Any]
    ) -> float:
        """Calculate overall search quality score."""
        if not results:
            return 0.0
        
        # Factors:
        # 1. Top results have required skills
        # 2. Score distribution (not all bunched together)
        # 3. Diversity of results
        
        quality_score = 0.0
        
        # Check skill matches in top 3
        top_skill_matches = 0
        for resume_data, score in results[:3]:
            if resume_data.get("skill_analysis", {}).get("match_percentage", 0) >= 80:
                top_skill_matches += 1
        
        quality_score += (top_skill_matches / 3) * 0.5
        
        # Check score distribution
        if len(results) > 1:
            scores = [score for _, score in results]
            score_range = max(scores) - min(scores)
            if score_range > 0.3:  # Good distribution
                quality_score += 0.3
        
        # Check if we have high-scoring results
        if any(score > 0.7 for _, score in results[:3]):
            quality_score += 0.2
        
        return min(1.0, quality_score)
    
    async def _quick_skill_search(
        self,
        db: AsyncSession,
        user_id: UUID,
        skills: List[str],
        limit: int
    ) -> List[Tuple[dict, float]]:
        """Quick search for exact skill matches."""
        # Build query for skill matches
        skill_conditions = []
        for skill in skills[:3]:  # Limit to first 3 skills for speed
            skill_conditions.append(
                func.cast(Resume.skills, SQLString).ilike(f'%"{skill}"%')
            )
        
        stmt = select(Resume).where(
            Resume.user_id == user_id,
            Resume.status == 'active',
            or_(*skill_conditions)
        ).limit(limit)
        
        result = await db.execute(stmt)
        resumes = result.scalars().all()
        
        # Convert to result format with basic scoring
        results = []
        for resume in resumes:
            resume_data = self._resume_to_dict(resume)
            
            # Count matching skills for basic score
            matching_count = 0
            if resume.skills:
                resume_skills_lower = [s.lower() for s in resume.skills]
                for skill in skills:
                    if any(skill in rs for rs in resume_skills_lower):
                        matching_count += 1
            
            score = matching_count / len(skills) if skills else 0.5
            results.append((resume_data, score))
        
        return results
    
    async def _basic_keyword_search(
        self,
        db: AsyncSession,
        query: str,
        user_id: UUID,
        limit: int
    ) -> List[Tuple[dict, float]]:
        """Basic keyword search on title and summary."""
        search_terms = query.lower().split()[:3]  # Limit terms for speed
        
        conditions = []
        for term in search_terms:
            pattern = f"%{term}%"
            conditions.extend([
                Resume.current_title.ilike(pattern),
                Resume.summary.ilike(pattern)
            ])
        
        stmt = select(Resume).where(
            Resume.user_id == user_id,
            Resume.status == 'active',
            or_(*conditions)
        ).limit(limit)
        
        result = await db.execute(stmt)
        resumes = result.scalars().all()
        
        # Basic scoring based on term matches
        results = []
        for resume in resumes:
            resume_data = self._resume_to_dict(resume)
            score = 0.3  # Base score
            
            # Boost for title matches
            if resume.current_title:
                title_lower = resume.current_title.lower()
                for term in search_terms:
                    if term in title_lower:
                        score += 0.2
            
            results.append((resume_data, min(score, 1.0)))
        
        return results
    
    async def _cache_results(
        self,
        query: str,
        user_id: UUID,
        results: List[Tuple[dict, float]]
    ):
        """Cache search results."""
        try:
            redis = await self._get_redis()
            if not redis:
                return
            
            cache_key = f"search:{user_id}:{query.lower()}"
            
            # Prepare data for caching (limit size)
            cache_data = []
            for resume_data, score in results[:20]:  # Cache top 20
                # Remove large fields for cache efficiency
                cached_resume = {
                    k: v for k, v in resume_data.items()
                    if k not in ["summary", "parsed_data", "raw_text"]
                }
                cache_data.append((cached_resume, score))
            
            # Store in Redis with TTL
            await redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(cache_data, default=str)
            )
            
            logger.info(f"Cached {len(cache_data)} results for '{query}'")
            
        except Exception as e:
            logger.error(f"Error caching results: {e}")
    
    async def _get_cached_results(
        self,
        query: str,
        user_id: UUID
    ) -> Optional[List[Tuple[dict, float]]]:
        """Get cached search results."""
        try:
            redis = await self._get_redis()
            if not redis:
                return None
            
            cache_key = f"search:{user_id}:{query.lower()}"
            cached = await redis.get(cache_key)
            
            if cached:
                data = json.loads(cached)
                # Convert back to tuples
                return [(item[0], item[1]) for item in data]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached results: {e}")
            return None


# Singleton instance
progressive_search = ProgressiveSearchEngine()