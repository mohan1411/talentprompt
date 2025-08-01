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
from app.services.async_query_parser import async_query_parser
from app.services.hybrid_search import hybrid_search
from app.services.gpt4_query_analyzer import gpt4_analyzer
from app.services.candidate_analytics import candidate_analytics_service
from app.services.career_dna import career_dna_service
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
        
        # Parse query once for all stages (use async parser with AI typo correction)
        try:
            parsed_query = await async_query_parser.parse_query_async(query)
            logger.info(f"[PROGRESSIVE] Using AI-powered query parser with corrections")
            logger.info(f"[PROGRESSIVE] Original query: '{query}'")
            logger.info(f"[PROGRESSIVE] Parsed skills: {parsed_query.get('skills', [])}")
            logger.info(f"[PROGRESSIVE] Corrected query: {parsed_query.get('corrected_query')}")
        except Exception as e:
            logger.warning(f"[PROGRESSIVE] AI parser failed, falling back to basic parser: {e}")
            parsed_query = query_parser.parse_query(query)
        
        required_skills = parsed_query["skills"]
        primary_skill = parsed_query.get("primary_skill")
        
        # Get advanced analysis using GPT4 for Mind Reader Search
        search_suggestions = []
        try:
            # Use corrected query if available, otherwise use original query
            query_for_analysis = parsed_query.get("corrected_query", query)
            
            # IMPORTANT: When we have a corrected query, we need to ensure the parsed_query
            # contains the corrected skills for the fallback enhanced parse
            if parsed_query.get("corrected_query") and parsed_query.get("corrected_query") != query:
                # Re-parse the corrected query to ensure we have the right skills
                from app.services.query_parser import query_parser as basic_parser
                corrected_parse = basic_parser.parse_query(parsed_query["corrected_query"])
                # Update the skills in parsed_query with the corrected ones
                if corrected_parse.get("skills"):
                    parsed_query["skills"] = corrected_parse["skills"]
                    parsed_query["primary_skill"] = corrected_parse.get("primary_skill")
                logger.info(f"[PROGRESSIVE] Updated parsed_query skills after correction: {parsed_query.get('skills')}")
            
            gpt4_analysis = await gpt4_analyzer.analyze_query(query_for_analysis)
            
            # Transform to frontend format, preferring GPT4 analysis when available
            frontend_query_analysis = {
                "primary_skills": gpt4_analysis.get("primary_skills", parsed_query.get("skills", [])),
                "secondary_skills": gpt4_analysis.get("secondary_skills", []),
                "implied_skills": gpt4_analysis.get("implied_skills", []),
                "experience_level": gpt4_analysis.get("experience_level", self._determine_experience_level(parsed_query)),
                "role_type": gpt4_analysis.get("role_type", parsed_query.get("roles", ["any"])[0] if parsed_query.get("roles") else "any"),
                "search_intent": gpt4_analysis.get("search_intent", "technical" if parsed_query.get("skills") else "general"),
                "corrected_query": parsed_query.get("corrected_query") if parsed_query.get("corrected_query") != query else None,
                "original_query": query if parsed_query.get("corrected_query") else None
            }
            
            # Get search suggestions
            search_suggestions = gpt4_analyzer.get_search_suggestions(gpt4_analysis)
            
            logger.info(f"[PROGRESSIVE] GPT4 analysis successful")
            logger.info(f"[PROGRESSIVE] Primary skills: {frontend_query_analysis['primary_skills']}")
            logger.info(f"[PROGRESSIVE] Secondary skills: {frontend_query_analysis['secondary_skills']}")
            logger.info(f"[PROGRESSIVE] Implied skills: {frontend_query_analysis['implied_skills']}")
            logger.info(f"[PROGRESSIVE] Suggestions: {search_suggestions}")
        except Exception as e:
            logger.warning(f"GPT4 analysis failed, using enhanced basic analysis: {e}")
            # Use the enhanced basic parse from GPT4 analyzer
            try:
                enhanced_basic = gpt4_analyzer._enhance_basic_parse(parsed_query)
                frontend_query_analysis = {
                    "primary_skills": enhanced_basic.get("primary_skills", parsed_query.get("skills", [])),
                    "secondary_skills": enhanced_basic.get("secondary_skills", []),
                    "implied_skills": enhanced_basic.get("implied_skills", []),
                    "experience_level": enhanced_basic.get("experience_level", self._determine_experience_level(parsed_query)),
                    "role_type": enhanced_basic.get("role_type", parsed_query.get("roles", ["any"])[0] if parsed_query.get("roles") else "any"),
                    "search_intent": enhanced_basic.get("search_intent", "technical" if parsed_query.get("skills") else "general"),
                    "corrected_query": parsed_query.get("corrected_query") if parsed_query.get("corrected_query") != query else None,
                    "original_query": query if parsed_query.get("corrected_query") else None
                }
                # Get suggestions from enhanced basic analysis
                search_suggestions = gpt4_analyzer.get_search_suggestions(enhanced_basic)
                logger.info(f"[PROGRESSIVE] Using enhanced basic analysis - secondary skills: {frontend_query_analysis['secondary_skills']}")
                
                # CRITICAL FIX: If we still have no secondary skills but we have primary skills,
                # force populate them based on the primary skills
                if (not frontend_query_analysis.get("secondary_skills") and 
                    frontend_query_analysis.get("primary_skills")):
                    logger.warning("[PROGRESSIVE] No secondary skills found, forcing population")
                    
                    # Manual skill mappings as last resort
                    skill_map = {
                        "javascript": ["react", "node.js", "typescript", "vue", "angular"],
                        "python": ["django", "flask", "fastapi", "pandas", "numpy"],
                        "java": ["spring", "spring boot", "hibernate", "maven", "gradle"],
                        "aws": ["docker", "terraform", "kubernetes", "lambda", "s3"],
                        "react": ["redux", "next.js", "styled-components", "webpack", "jest"],
                        "go": ["microservices", "grpc", "docker", "kubernetes", "prometheus"],
                        "golang": ["microservices", "grpc", "docker", "kubernetes", "prometheus"],
                    }
                    
                    for primary_skill in frontend_query_analysis["primary_skills"]:
                        skill_lower = primary_skill.lower()
                        if skill_lower in skill_map:
                            frontend_query_analysis["secondary_skills"] = skill_map[skill_lower]
                            logger.info(f"[PROGRESSIVE] Force populated secondary skills: {skill_map[skill_lower]}")
                            break
            except Exception as e2:
                logger.error(f"Enhanced basic analysis also failed: {e2}")
                # Ultimate fallback
                frontend_query_analysis = {
                    "primary_skills": parsed_query.get("skills", []),
                    "secondary_skills": [],
                    "implied_skills": [],
                    "experience_level": self._determine_experience_level(parsed_query),
                    "role_type": parsed_query.get("roles", ["any"])[0] if parsed_query.get("roles") else "any",
                    "search_intent": "technical" if parsed_query.get("skills") else "general",
                    "corrected_query": parsed_query.get("corrected_query") if parsed_query.get("corrected_query") != query else None,
                    "original_query": query if parsed_query.get("corrected_query") else None
                }
        
        logger.info(f"Progressive search started: '{query}' for user {user_id}")
        print(f"\n[PROGRESSIVE SEARCH] Started for query: '{query}'")
        
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
            "parsed_query": frontend_query_analysis,
            "suggestions": search_suggestions,
            "results": stage1_results,
            "count": len(stage1_results),
            "timing_ms": int((time.time() - start_time) * 1000),
            "is_final": False
        }
        
        # Stage 2: Enhanced Results (Vector Search + Skill Matching)
        logger.info(f"[PROGRESSIVE] Starting Stage 2 for query: {query}")
        stage2_results = await self._stage2_enhanced_results(
            db, query, user_id, limit * 2, filters, parsed_query, stage1_results
        )
        logger.info(f"[PROGRESSIVE] Stage 2 returned {len(stage2_results)} results")
        
        # Merge and deduplicate results
        merged_results = self._merge_results(stage1_results, stage2_results, limit)
        
        print(f"[PROGRESSIVE] Stage 2 yielding {len(merged_results)} results")
        if merged_results and len(merged_results) > 0:
            first_result = merged_results[0][0]
            print(f"[PROGRESSIVE] First result has availability: {first_result.get('availability_score')}")
        
        yield {
            "stage": "enhanced", 
            "stage_number": 2,
            "total_stages": 3,
            "search_id": search_id,
            "query": query,
            "parsed_query": frontend_query_analysis,
            "suggestions": search_suggestions,
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
            "parsed_query": frontend_query_analysis,
            "suggestions": search_suggestions,
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
        logger.info(f"[STAGE2] Performing hybrid search for query: {query}")
        hybrid_results = await hybrid_search.search(
            db=db,
            query=query,
            user_id=str(user_id),
            limit=limit,
            filters=filters,
            use_synonyms=True
        )
        
        logger.info(f"[STAGE2] Hybrid search returned {len(hybrid_results) if hybrid_results else 0} results")
        
        if not hybrid_results:
            logger.warning("[STAGE2] No hybrid results found, returning empty")
            return []
        
        # Apply skill-based scoring enhancements
        enhanced_results = []
        for resume_data, hybrid_score in hybrid_results:
            # Add additional skill analysis
            skill_analysis = self._analyze_skill_match(resume_data, parsed_query)
            resume_data["skill_analysis"] = skill_analysis
            
            # Add candidate analytics (availability, learning velocity, etc.)
            try:
                print(f"[ANALYTICS] Calculating for {resume_data.get('first_name')} {resume_data.get('last_name')}")
                resume_data["availability_score"] = candidate_analytics_service.calculate_availability_score(resume_data)
                resume_data["learning_velocity"] = candidate_analytics_service.calculate_learning_velocity(resume_data)
                resume_data["career_trajectory"] = candidate_analytics_service.analyze_career_trajectory(resume_data)
                print(f"[ANALYTICS] Success: availability={resume_data.get('availability_score')}, velocity={resume_data.get('learning_velocity')}")
            except Exception as e:
                print(f"[ANALYTICS] ERROR: {e}")
                import traceback
                print(traceback.format_exc())
            
            # Add career DNA profile
            try:
                career_dna = career_dna_service.extract_career_dna(resume_data)
                resume_data["career_dna"] = {
                    "pattern": career_dna["pattern_type"],
                    "progression_speed": career_dna["progression_speed"],
                    "skill_evolution": career_dna["skill_evolution"],
                    "strengths": career_dna["strengths"],
                    "unique_traits": career_dna["unique_traits"],
                    "growth_indicators": career_dna["growth_indicators"]
                }
                logger.info(f"Added career DNA for {resume_data.get('first_name')} {resume_data.get('last_name')}: pattern={career_dna['pattern_type']}")
            except Exception as e:
                logger.error(f"Error extracting career DNA: {e}")
                resume_data["career_dna"] = None
            
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
        # First add basic analysis and ensure all results have analytics
        for resume_data, score in results:
            # Add skill match details
            skill_analysis = self._analyze_skill_match(resume_data, parsed_query)
            resume_data["skill_analysis"] = skill_analysis
            
            # Add analytics if not already present (for Stage 1 results)
            if resume_data.get("availability_score") is None:
                try:
                    print(f"[STAGE3] Adding missing analytics for {resume_data.get('first_name')} {resume_data.get('last_name')}")
                    resume_data["availability_score"] = candidate_analytics_service.calculate_availability_score(resume_data)
                    resume_data["learning_velocity"] = candidate_analytics_service.calculate_learning_velocity(resume_data)
                    resume_data["career_trajectory"] = candidate_analytics_service.analyze_career_trajectory(resume_data)
                    
                    # Also add career DNA
                    career_dna = career_dna_service.extract_career_dna(resume_data)
                    resume_data["career_dna"] = {
                        "pattern": career_dna["pattern_type"],
                        "progression_speed": career_dna["progression_speed"],
                        "skill_evolution": career_dna["skill_evolution"],
                        "strengths": career_dna["strengths"],
                        "unique_traits": career_dna["unique_traits"],
                        "growth_indicators": career_dna["growth_indicators"]
                    }
                except Exception as e:
                    print(f"[STAGE3] Error adding analytics: {e}")
        
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
        # Create a map to store the best version of each result
        results_map = {}
        
        # First add stage1 results
        for resume_data, score in stage1:
            resume_id = resume_data["id"]
            results_map[resume_id] = (resume_data, score)
        
        # Then add/update with stage2 results (which have analytics)
        for resume_data, score in stage2:
            resume_id = resume_data["id"]
            if resume_id in results_map:
                # Merge the data, preserving analytics from stage2
                existing_data, existing_score = results_map[resume_id]
                # Update with enhanced data from stage2
                merged_data = {**existing_data, **resume_data}
                # Use the better score
                best_score = max(score, existing_score)
                results_map[resume_id] = (merged_data, best_score)
            else:
                results_map[resume_id] = (resume_data, score)
        
        # Convert back to list and sort by score
        merged = list(results_map.values())
        merged.sort(key=lambda x: x[1], reverse=True)
        
        print(f"[MERGE] Merged {len(merged)} results")
        if merged:
            first = merged[0][0]
            print(f"[MERGE] First merged result has availability: {first.get('availability_score')}")
        
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
    
    def _determine_experience_level(self, parsed_query: Dict[str, Any]) -> str:
        """Determine experience level from parsed query."""
        seniority = parsed_query.get("seniority", "").lower() if parsed_query.get("seniority") else ""
        years = parsed_query.get("experience_years")
        
        if seniority in ["senior", "sr", "lead", "principal", "staff", "architect"]:
            return "senior"
        elif seniority in ["junior", "jr", "entry", "graduate", "intern"]:
            return "junior"
        elif seniority in ["mid", "intermediate"]:
            return "mid"
        elif years:
            if years >= 7:
                return "senior"
            elif years >= 3:
                return "mid"
            else:
                return "junior"
        else:
            return "any"


# Singleton instance
progressive_search = ProgressiveSearchEngine()