"""Search service using Qdrant vector database."""

import logging
import re
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.resume import Resume
from app.services.embeddings import embedding_service
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
        """Search resumes using vector similarity.
        
        Args:
            db: Database session
            query: Search query text
            limit: Maximum number of results
            filters: Optional filters (location, skills, experience)
            
        Returns:
            List of tuples (resume_data, similarity_score)
        """
        # Generate embedding for the query
        query_embedding = await embedding_service.generate_embedding(query)
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []
        
        # Build the search query
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        # Base query with vector similarity
        sql_query = """
            SELECT 
                r.id,
                r.first_name,
                r.last_name,
                r.email,
                r.phone,
                r.location,
                r.current_title,
                r.summary,
                r.years_experience,
                r.skills,
                r.keywords,
                r.created_at,
                r.view_count,
                1 - (r.embedding <=> CAST(:query_embedding AS vector(1536))) AS similarity
            FROM resumes r
            WHERE 
                r.embedding IS NOT NULL
                AND r.status = 'active'
                AND r.parse_status = 'completed'
                AND 1 - (r.embedding <=> CAST(:query_embedding AS vector(1536))) > 0.25
        """
        
        # Add filters
        params = {"query_embedding": embedding_str}
        filter_conditions = []
        
        if filters:
            if filters.get("location"):
                filter_conditions.append("r.location ILIKE :location")
                params["location"] = f"%{filters['location']}%"
            
            if filters.get("min_experience"):
                filter_conditions.append("r.years_experience >= :min_exp")
                params["min_exp"] = filters["min_experience"]
            
            if filters.get("max_experience"):
                filter_conditions.append("r.years_experience <= :max_exp")
                params["max_exp"] = filters["max_experience"]
            
            if filters.get("skills"):
                # Check if any of the required skills are in the resume skills array
                # Use exact matching for skill filters (case-insensitive)
                skill_conditions = []
                for i, skill in enumerate(filters["skills"]):
                    param_name = f"skill_{i}"
                    # Use exact match (case-insensitive) instead of LIKE for skill filters
                    skill_conditions.append(f"EXISTS (SELECT 1 FROM json_array_elements_text(r.skills::json) s WHERE LOWER(s) = LOWER(:{param_name}))")
                    params[param_name] = skill
                
                if skill_conditions:
                    filter_conditions.append(f"({' OR '.join(skill_conditions)})")
        
        if filter_conditions:
            sql_query += " AND " + " AND ".join(filter_conditions)
        
        # Extract key skills/technologies from the query
        skill_keywords = []
        tech_keywords = ["python", "java", "javascript", "react", "angular", "vue", "django", "flask", "spring", 
                        "aws", "azure", "gcp", "docker", "kubernetes", "ai", "ml", "machine learning", "data science",
                        "devops", "backend", "frontend", "fullstack", "api", "rest", "graphql", "sql", "nosql",
                        "mongodb", "postgresql", "mysql", "redis", "elasticsearch", "kafka", "rabbitmq"]
        
        query_lower = query.lower()
        for tech in tech_keywords:
            if tech in query_lower:
                skill_keywords.append(tech)
        
        # If we found specific skills, add keyword filtering
        # Only apply this if NOT using skill filters (to avoid double filtering)
        if skill_keywords and not (filters and filters.get("skills")):
            skill_conditions = []
            for i, skill in enumerate(skill_keywords):
                param_name = f"keyword_{i}"
                # For keyword search from query, be more specific with matching
                # Match whole words for common terms like "java" to avoid matching "javascript"
                if skill.lower() in ["java", "c", "go", "rust"]:
                    # Use word boundary matching for short language names
                    skill_conditions.append(f"""(
                        r.current_title ~* '\\y{skill}\\y'
                        OR r.summary ~* '\\y{skill}\\y' 
                        OR EXISTS (SELECT 1 FROM json_array_elements_text(r.skills::json) s WHERE s ~* '\\y{skill}\\y')
                    )""")
                else:
                    # Use LIKE for longer terms
                    skill_conditions.append(f"""(
                        LOWER(r.current_title) LIKE :{param_name}
                        OR LOWER(r.summary) LIKE :{param_name} 
                        OR EXISTS (SELECT 1 FROM json_array_elements_text(r.skills::json) s WHERE LOWER(s) LIKE :{param_name})
                    )""")
                    params[param_name] = f"%{skill}%"
            
            # Remove the similarity threshold from WHERE and add keyword conditions
            sql_query = sql_query.replace(
                "AND 1 - (r.embedding <=> CAST(:query_embedding AS vector(1536))) > 0.25",
                ""
            )
            
            # Add keyword conditions
            if filter_conditions:
                sql_query += " AND " + " AND ".join(filter_conditions)
            
            sql_query += f" AND ({' OR '.join(skill_conditions)})"
            
            # Order by similarity and limit
            sql_query += """
                ORDER BY similarity DESC
                LIMIT :limit
            """
            params["limit"] = limit
            logger.info(f"Using keyword-enhanced search for: {skill_keywords}")
        else:
            # No keywords found, use regular vector search with filters
            if filter_conditions:
                sql_query += " AND " + " AND ".join(filter_conditions)
            
            sql_query += """
                ORDER BY similarity DESC
                LIMIT :limit
            """
            params["limit"] = limit
            logger.info("Using vector-only search")
        
        logger.info(f"Search query: '{query}' - using {'keyword + vector' if skill_keywords else 'vector only'} search")
        if filters and filters.get("skills"):
            logger.info(f"Using exact skill filters: {filters['skills']}")
        
        # Execute query
        try:
            result = await db.execute(text(sql_query), params)
            rows = result.fetchall()
            logger.info(f"Found {len(rows)} results above similarity threshold")
            
            # Convert to list of tuples
            results = []
            for row in rows:
                resume_data = {
                    "id": str(row.id),
                    "first_name": row.first_name,
                    "last_name": row.last_name,
                    "email": row.email,
                    "phone": row.phone,
                    "location": row.location,
                    "current_title": row.current_title,
                    "summary": row.summary,
                    "years_experience": row.years_experience,
                    "skills": row.skills or [],
                    "keywords": row.keywords or [],
                    "created_at": row.created_at,
                    "view_count": row.view_count
                }
                similarity = float(row.similarity)
                # Log similarity scores for debugging
                logger.info(f"Resume {row.first_name} {row.last_name}: similarity = {similarity:.3f}")
                results.append((resume_data, similarity))
            
            # Update search appearance count for returned resumes
            if results:
                resume_ids = [r[0]["id"] for r in results]
                await self._update_search_appearances(db, resume_ids)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching resumes: {e}")
            return []
    
    async def _update_search_appearances(
        self, db: AsyncSession, resume_ids: List[str]
    ) -> None:
        """Update search appearance count for resumes."""
        try:
            from app import crud
            await crud.resume.increment_search_appearance(db, resume_ids=resume_ids)
        except Exception as e:
            logger.error(f"Error updating search appearances: {e}")
    
    async def get_similar_resumes(
        self,
        db: AsyncSession,
        resume_id: str,
        limit: int = 5
    ) -> List[Tuple[dict, float]]:
        """Find resumes similar to a given resume.
        
        Args:
            db: Database session
            resume_id: ID of the reference resume
            limit: Maximum number of results
            
        Returns:
            List of tuples (resume_data, similarity_score)
        """
        # Get the reference resume's embedding
        sql_query = """
            SELECT embedding
            FROM resumes
            WHERE id = :resume_id AND embedding IS NOT NULL
        """
        
        result = await db.execute(text(sql_query), {"resume_id": resume_id})
        row = result.fetchone()
        
        if not row or not row.embedding:
            logger.warning(f"Resume {resume_id} has no embedding")
            return []
        
        # Find similar resumes
        sql_query = """
            SELECT 
                r.id,
                r.first_name,
                r.last_name,
                r.current_title,
                r.location,
                r.years_experience,
                r.skills,
                1 - (r.embedding <=> CAST(:ref_embedding AS vector)) AS similarity
            FROM resumes r
            WHERE 
                r.id != :resume_id
                AND r.embedding IS NOT NULL
                AND r.status = 'active'
                AND r.parse_status = 'completed'
            ORDER BY similarity DESC
            LIMIT :limit
        """
        
        params = {
            "ref_embedding": row.embedding,
            "resume_id": resume_id,
            "limit": limit
        }
        
        result = await db.execute(text(sql_query), params)
        rows = result.fetchall()
        
        results = []
        for row in rows:
            resume_data = {
                "id": str(row.id),
                "first_name": row.first_name,
                "last_name": row.last_name,
                "current_title": row.current_title,
                "location": row.location,
                "years_experience": row.years_experience,
                "skills": row.skills or []
            }
            similarity = float(row.similarity)
            results.append((resume_data, similarity))
        
        return results
    
    async def get_search_suggestions(
        self,
        db: AsyncSession,
        partial_query: str
    ) -> List[dict]:
        """Generate intelligent search suggestions based on partial query.
        
        Args:
            db: Database session
            partial_query: Partial search query from user
            
        Returns:
            List of search suggestions with counts
        """
        suggestions = []
        query_lower = partial_query.lower().strip()
        
        # Identify query intent
        intent = await self._identify_search_intent(query_lower)
        
        # Get dynamic suggestions based on actual database content
        dynamic_suggestions = await self._get_dynamic_suggestions(db, query_lower, intent)
        
        # If we have good dynamic suggestions, prioritize them
        if dynamic_suggestions:
            return dynamic_suggestions[:8]
        
        # Check for common typos and fix them
        typo_corrections = {
            "experienced": "experience",
            "developper": "developer",
            "enginer": "engineer",
            "backendd": "backend",
            "frontendd": "frontend",
        }
        
        # Fix typos in query
        corrected_query = partial_query
        for typo, correction in typo_corrections.items():
            if typo in query_lower and correction not in query_lower:
                corrected_query = corrected_query.replace(typo, correction)
                query_lower = corrected_query.lower()
        
        # Check for limit patterns (top 5, first 10, etc.)
        limit_patterns = [
            r'\btop (\d+)\b',
            r'\bfirst (\d+)\b',
            r'\bshow (?:me )?(\d+)\b',
        ]
        
        has_limit = False
        limit_prefix = ""
        for pattern in limit_patterns:
            match = re.search(pattern, query_lower)
            if match:
                has_limit = True
                limit_prefix = match.group(0)
                break
        
        # Common role-based suggestions
        role_suggestions = {
            "python": ["Python Developer", "Senior Python Engineer", "Python Backend Developer", "Python Full Stack Developer"],
            "java": ["Java Developer", "Senior Java Engineer", "Java Backend Developer", "Java Spring Developer"],
            "react": ["React Developer", "React Frontend Engineer", "React Native Developer", "Senior React Developer"],
            "data": ["Data Scientist", "Data Engineer", "Data Analyst", "Senior Data Scientist"],
            "devops": ["DevOps Engineer", "Senior DevOps Engineer", "DevOps Architect", "Cloud DevOps Engineer"],
            "frontend": ["Frontend Developer", "Frontend Engineer", "Senior Frontend Developer", "UI/UX Developer"],
            "backend": ["Backend Developer", "Backend Engineer", "Senior Backend Developer", "API Developer"],
            "fullstack": ["Full Stack Developer", "Full Stack Engineer", "Senior Full Stack Developer"],
            "machine": ["Machine Learning Engineer", "ML Engineer", "Machine Learning Scientist", "AI/ML Engineer"],
            "cloud": ["Cloud Engineer", "Cloud Architect", "AWS Engineer", "Azure Engineer"],
            "senior": ["Senior Software Engineer", "Senior Developer", "Senior Full Stack Engineer", "Senior Backend Engineer"],
            "lead": ["Lead Developer", "Lead Engineer", "Tech Lead", "Lead Software Engineer"],
            "manager": ["Engineering Manager", "Product Manager", "Project Manager", "Technical Manager"],
            "fintech": ["Fintech Developer", "Financial Software Engineer", "Payments Developer", "Blockchain Developer"],
            "banking": ["Banking Software Developer", "Core Banking Engineer", "Financial Systems Developer", "Treasury Systems Engineer"],
        }
        
        # Skill-based suggestions
        skill_suggestions = {
            "aws": ["developers with AWS", "AWS certified engineers", "AWS cloud architects"],
            "docker": ["developers with Docker", "Docker and Kubernetes", "containerization experts"],
            "kubernetes": ["Kubernetes engineers", "K8s specialists", "container orchestration experts"],
            "microservices": ["microservices architects", "distributed systems engineers"],
            "ai": ["AI engineers", "artificial intelligence specialists", "AI/ML developers"],
            "blockchain": ["blockchain developers", "Web3 engineers", "smart contract developers"],
            "fintech": ["developers with fintech experience", "fintech engineers", "payment systems developers"],
            "banking": ["developers with banking experience", "core banking engineers", "financial services developers"],
        }
        
        # Experience-based suggestions
        if any(word in query_lower for word in ["senior", "sr", "lead", "principal"]):
            experience_suggestions = [
                f"{partial_query} with 5+ years experience",
                f"{partial_query} with 8+ years experience",
                f"{partial_query} with leadership experience"
            ]
        elif any(word in query_lower for word in ["junior", "jr", "entry"]):
            experience_suggestions = [
                f"{partial_query} with 0-2 years experience",
                f"{partial_query} fresh graduates",
                f"{partial_query} entry level"
            ]
        else:
            experience_suggestions = []
        
        # Generate suggestions based on partial query
        all_suggestions = []
        
        # Check for keywords in the query
        query_words = query_lower.split()
        
        # Check role suggestions - look for any matching keywords in the query
        for key, values in role_suggestions.items():
            if key in query_lower or any(key.startswith(word) or word.startswith(key) for word in query_words if len(word) > 2):
                for value in values[:3]:  # Limit to 3 suggestions per category
                    # If query has a limit prefix (top 5, first 10), preserve it
                    if has_limit:
                        suggestion_text = f"{limit_prefix} {value.lower()}"
                    else:
                        suggestion_text = value
                    all_suggestions.append((suggestion_text, "role"))
        
        # Check skill suggestions - look for any matching keywords in the query
        for key, values in skill_suggestions.items():
            if key in query_lower or any(key.startswith(word) or word.startswith(key) for word in query_words if len(word) > 2):
                for value in values[:2]:  # Limit to 2 suggestions per skill
                    # If query has a limit prefix (top 5, first 10), preserve it
                    if has_limit:
                        suggestion_text = f"{limit_prefix} {value.lower()}"
                    else:
                        suggestion_text = value
                    all_suggestions.append((suggestion_text, "skill"))
        
        # Add experience suggestions
        for exp_suggestion in experience_suggestions[:2]:
            all_suggestions.append((exp_suggestion, "experience"))
        
        # If no matches found, create intelligent generic suggestions
        if not all_suggestions and len(query_lower) >= 3:
            # Check if query already contains role terms
            role_terms = ["developer", "engineer", "architect", "designer", "analyst", "scientist", "manager"]
            has_role = any(term in query_lower for term in role_terms)
            
            # Check for domain keywords
            domain_keywords = ["fintech", "banking", "healthcare", "ecommerce", "saas", "mobile", "web", "cloud"]
            domains_in_query = [domain for domain in domain_keywords if domain in query_lower]
            
            if has_role:
                # Query already has a role, don't append another
                if corrected_query != partial_query:
                    # If we corrected a typo, suggest the corrected version
                    all_suggestions.append((corrected_query, "role"))
                
                # Add experience level variations
                if "senior" not in query_lower and "junior" not in query_lower:
                    all_suggestions.append((f"senior {corrected_query}", "experience"))
                    all_suggestions.append((f"junior {corrected_query}", "experience"))
                
                # If domains found, suggest focused roles
                if domains_in_query:
                    for domain in domains_in_query:
                        if domain == "fintech":
                            all_suggestions.append(("fintech software engineer", "role"))
                            all_suggestions.append(("banking technology specialist", "role"))
                        elif domain == "banking":
                            all_suggestions.append(("banking software developer", "role"))
                            all_suggestions.append(("financial systems engineer", "role"))
            else:
                # No role in query, safe to append
                if has_limit:
                    # Clean query by removing the limit prefix for base suggestions
                    base_query = corrected_query.replace(limit_prefix, '').strip()
                    all_suggestions = [
                        (f"{limit_prefix} {base_query} developers", "role"),
                        (f"{limit_prefix} {base_query} engineers", "role"),
                        (f"{limit_prefix} senior {base_query} developers", "experience"),
                    ]
                else:
                    all_suggestions = [
                        (f"{corrected_query} developer", "role"),
                        (f"{corrected_query} engineer", "role"),
                        (f"senior {corrected_query} developer", "experience"),
                    ]
        
        # Count matches for each suggestion (simplified version)
        for suggestion_text, category in all_suggestions[:8]:  # Limit total suggestions
            # In a real implementation, we would run actual count queries
            # For now, we'll use estimates based on common patterns
            count = await self._estimate_candidate_count(db, suggestion_text)
            
            # For display purposes, show actual count up to 20, then "20+"
            # If the suggestion contains a limit (top 5, first 10), use that as the display count
            if has_limit:
                limit_match = re.search(r'\b(\d+)\b', suggestion_text)
                if limit_match:
                    requested_limit = int(limit_match.group(1))
                    display_count = min(count, requested_limit)
                else:
                    display_count = count if count <= 20 else 20
            else:
                display_count = count if count <= 20 else 20
            
            suggestions.append({
                "query": suggestion_text,
                "count": display_count,
                "confidence": 0.85 if category == "role" else 0.75,
                "category": category
            })
        
        return suggestions
    
    async def _estimate_candidate_count(
        self,
        db: AsyncSession,
        query: str
    ) -> int:
        """Estimate the number of candidates matching a query.
        
        Uses the same logic as actual search for accurate counts.
        """
        # Extract tech keywords same as in search
        tech_keywords = ["python", "java", "javascript", "react", "angular", "vue", "django", "flask", "spring", 
                        "aws", "azure", "gcp", "docker", "kubernetes", "ai", "ml", "machine learning", "data science",
                        "devops", "backend", "frontend", "fullstack", "api", "rest", "graphql", "sql", "nosql",
                        "mongodb", "postgresql", "mysql", "redis", "elasticsearch", "kafka", "rabbitmq"]
        
        query_lower = query.lower()
        found_keywords = [tech for tech in tech_keywords if tech in query_lower]
        
        if found_keywords:
            # If tech keywords found, count only resumes with those keywords
            conditions = []
            params = {}
            for i, keyword in enumerate(found_keywords):
                param_name = f"keyword_{i}"
                conditions.append(f"""(
                    LOWER(current_title) LIKE :{param_name}
                    OR LOWER(summary) LIKE :{param_name}
                    OR EXISTS (SELECT 1 FROM json_array_elements_text(skills::json) s WHERE LOWER(s) LIKE :{param_name})
                )""")
                params[param_name] = f"%{keyword}%"
            
            sql_query = f"""
                SELECT COUNT(*) as count
                FROM resumes
                WHERE status = 'active'
                AND parse_status = 'completed'
                AND embedding IS NOT NULL
                AND ({' OR '.join(conditions)})
            """
        else:
            # For non-tech queries, count all active resumes with embeddings
            sql_query = """
                SELECT COUNT(*) as count
                FROM resumes
                WHERE status = 'active'
                AND parse_status = 'completed'
                AND embedding IS NOT NULL
            """
            params = {}
        
        result = await db.execute(text(sql_query), params)
        count = result.scalar() or 0
        
        # Apply role-based heuristics
        if "senior" in query_lower:
            count = int(count * 0.4)
        elif "junior" in query_lower:
            count = int(count * 0.25)
        elif "lead" in query_lower or "principal" in query_lower:
            count = int(count * 0.15)
        
        return max(1, count)  # Always show at least 1
    
    async def _identify_search_intent(self, query: str) -> dict:
        """Identify the intent behind a search query.
        
        Returns dict with intent type and metadata.
        """
        intent = {
            "type": "general",
            "has_role": False,
            "has_skill": False,
            "has_experience": False,
            "has_location": False,
            "has_limit": False,
            "components": []
        }
        
        # Role detection
        role_terms = ["developer", "engineer", "architect", "designer", "analyst", 
                     "scientist", "manager", "lead", "director", "specialist"]
        for term in role_terms:
            if term in query:
                intent["has_role"] = True
                intent["components"].append({"type": "role", "value": term})
                
        # Skill detection
        tech_keywords = ["python", "java", "javascript", "react", "angular", "vue", 
                        "django", "flask", "spring", "aws", "azure", "docker", 
                        "kubernetes", "sql", "nosql", "machine learning", "ai"]
        for tech in tech_keywords:
            if tech in query:
                intent["has_skill"] = True
                intent["components"].append({"type": "skill", "value": tech})
        
        # Experience level detection
        exp_keywords = ["senior", "junior", "lead", "principal", "entry", "mid-level"]
        for exp in exp_keywords:
            if exp in query:
                intent["has_experience"] = True
                intent["components"].append({"type": "experience", "value": exp})
        
        # Location detection
        location_keywords = ["remote", "onsite", "hybrid", "relocate"]
        for loc in location_keywords:
            if loc in query:
                intent["has_location"] = True
                intent["components"].append({"type": "location", "value": loc})
        
        # Limit detection
        if re.search(r'\b(top|first|show)\s+\d+\b', query):
            intent["has_limit"] = True
            intent["type"] = "limited"
        
        # Determine primary intent type
        if intent["has_skill"] and intent["has_role"]:
            intent["type"] = "specific_role"
        elif intent["has_skill"]:
            intent["type"] = "skill_search"
        elif intent["has_role"]:
            intent["type"] = "role_search"
        elif intent["has_location"]:
            intent["type"] = "location_search"
            
        return intent
    
    async def _get_dynamic_suggestions(
        self, 
        db: AsyncSession, 
        query: str,
        intent: dict
    ) -> List[dict]:
        """Generate suggestions based on actual database content and intent."""
        suggestions = []
        
        try:
            # Get popular skills related to the query
            if intent["has_skill"] or intent["type"] == "skill_search":
                skill_suggestions = await self._get_skill_based_suggestions(db, query)
                suggestions.extend(skill_suggestions)
            
            # Get role-based suggestions from actual titles
            if intent["has_role"] or intent["type"] == "role_search":
                role_suggestions = await self._get_role_based_suggestions(db, query)
                suggestions.extend(role_suggestions)
            
            # Get combination suggestions (skill + role)
            if intent["type"] == "specific_role":
                combo_suggestions = await self._get_combination_suggestions(db, query, intent)
                suggestions.extend(combo_suggestions)
            
            # Get trending searches
            if len(suggestions) < 4:
                trending = await self._get_trending_suggestions(db, query)
                suggestions.extend(trending)
            
            # Remove duplicates and limit
            seen = set()
            unique_suggestions = []
            for s in suggestions:
                if s["query"] not in seen:
                    seen.add(s["query"])
                    unique_suggestions.append(s)
                    
            return unique_suggestions[:8]
            
        except Exception as e:
            logger.error(f"Error getting dynamic suggestions: {e}")
            return []
    
    async def _get_skill_based_suggestions(
        self, 
        db: AsyncSession, 
        query: str
    ) -> List[dict]:
        """Get suggestions based on skills in the database."""
        suggestions = []
        
        # Query to find related skills that often appear together
        sql_query = """
            WITH skill_pairs AS (
                SELECT 
                    s1.skill_value as skill1,
                    s2.skill_value as skill2,
                    COUNT(*) as pair_count
                FROM 
                    (SELECT LOWER(json_array_elements_text(skills::json)) as skill_value, id 
                     FROM resumes WHERE status = 'active') s1
                JOIN 
                    (SELECT LOWER(json_array_elements_text(skills::json)) as skill_value, id 
                     FROM resumes WHERE status = 'active') s2
                ON s1.id = s2.id AND s1.skill_value != s2.skill_value
                WHERE s1.skill_value LIKE :query_pattern
                GROUP BY s1.skill_value, s2.skill_value
                ORDER BY pair_count DESC
                LIMIT 10
            )
            SELECT DISTINCT skill2, SUM(pair_count) as total_count
            FROM skill_pairs
            GROUP BY skill2
            ORDER BY total_count DESC
            LIMIT 5
        """
        
        result = await db.execute(
            text(sql_query), 
            {"query_pattern": f"%{query}%"}
        )
        related_skills = result.fetchall()
        
        for skill, count in related_skills:
            # Create suggestions like "Python + Django developers"
            if skill != query.lower():
                suggestions.append({
                    "query": f"{query} {skill} developer",
                    "count": min(20, count),
                    "confidence": 0.9,
                    "category": "skill"
                })
        
        return suggestions
    
    async def _get_role_based_suggestions(
        self, 
        db: AsyncSession, 
        query: str
    ) -> List[dict]:
        """Get suggestions based on actual job titles in database."""
        suggestions = []
        
        # Find popular job titles matching the query
        sql_query = """
            SELECT 
                current_title,
                COUNT(*) as count
            FROM resumes
            WHERE 
                status = 'active' 
                AND parse_status = 'completed'
                AND LOWER(current_title) LIKE :query_pattern
            GROUP BY current_title
            ORDER BY count DESC
            LIMIT 5
        """
        
        result = await db.execute(
            text(sql_query),
            {"query_pattern": f"%{query}%"}
        )
        titles = result.fetchall()
        
        for title, count in titles:
            suggestions.append({
                "query": title,
                "count": min(20, count),
                "confidence": 0.95,
                "category": "role"
            })
        
        return suggestions
    
    async def _get_combination_suggestions(
        self,
        db: AsyncSession,
        query: str,
        intent: dict
    ) -> List[dict]:
        """Get suggestions for skill + role combinations."""
        suggestions = []
        
        # Extract skills and roles from intent
        skills = [c["value"] for c in intent["components"] if c["type"] == "skill"]
        roles = [c["value"] for c in intent["components"] if c["type"] == "role"]
        
        if skills and roles:
            # Find candidates with both skill and role
            for skill in skills[:2]:
                for role in roles[:2]:
                    count = await self._estimate_candidate_count(db, f"{skill} {role}")
                    if count > 0:
                        suggestions.append({
                            "query": f"{skill} {role}",
                            "count": min(20, count),
                            "confidence": 0.85,
                            "category": "role"
                        })
                        
                        # Add experience variations
                        suggestions.append({
                            "query": f"senior {skill} {role}",
                            "count": min(10, count // 2),
                            "confidence": 0.80,
                            "category": "experience"
                        })
        
        return suggestions
    
    async def _get_trending_suggestions(
        self,
        db: AsyncSession,
        query: str
    ) -> List[dict]:
        """Get trending search suggestions based on recent activity."""
        suggestions = []
        
        # For now, return popular generic searches
        # In a full implementation, this would track actual search history
        trending_searches = [
            ("Full Stack Developer", 20, "role"),
            ("Python Developer", 20, "role"),
            ("React Developer", 18, "role"),
            ("DevOps Engineer", 15, "role"),
            ("Data Scientist", 12, "role"),
        ]
        
        for search, count, category in trending_searches:
            if query.lower() in search.lower():
                suggestions.append({
                    "query": search,
                    "count": count,
                    "confidence": 0.75,
                    "category": category
                })
        
        return suggestions[:3]
    
    async def get_popular_tags(
        self,
        db: AsyncSession,
        limit: int = 30
    ) -> List[dict]:
        """Get popular skills/tags from resumes with counts.
        
        Args:
            db: Database session
            limit: Maximum number of tags to return
            
        Returns:
            List of tags with counts and categories
        """
        # Query to get skill counts
        sql_query = """
            WITH skill_counts AS (
                SELECT 
                    LOWER(skill_value) as skill,
                    COUNT(*) as count
                FROM resumes r,
                    json_array_elements_text(r.skills) as skill_value
                WHERE r.status = 'active'
                AND r.parse_status = 'completed'
                GROUP BY LOWER(skill_value)
                ORDER BY count DESC
                LIMIT :limit
            )
            SELECT skill, count FROM skill_counts
        """
        
        result = await db.execute(text(sql_query), {"limit": limit})
        rows = result.fetchall()
        
        # Categorize skills
        categories = {
            # Programming Languages
            "python": "language",
            "java": "language", 
            "javascript": "language",
            "typescript": "language",
            "c++": "language",
            "c#": "language",
            "go": "language",
            "rust": "language",
            "php": "language",
            "ruby": "language",
            
            # Frontend
            "react": "frontend",
            "angular": "frontend",
            "vue": "frontend",
            "html": "frontend",
            "html5": "frontend",
            "css": "frontend",
            "css3": "frontend",
            "sass": "frontend",
            "tailwind": "frontend",
            
            # Backend/Frameworks
            "django": "framework",
            "flask": "framework",
            "fastapi": "framework",
            "spring": "framework",
            "express": "framework",
            "rails": "framework",
            ".net": "framework",
            
            # Databases
            "mysql": "database",
            "postgresql": "database",
            "mongodb": "database",
            "redis": "database",
            "elasticsearch": "database",
            "cassandra": "database",
            
            # Cloud/DevOps
            "aws": "cloud",
            "azure": "cloud",
            "gcp": "cloud",
            "docker": "devops",
            "kubernetes": "devops",
            "jenkins": "devops",
            "terraform": "devops",
            "ansible": "devops",
            "ci/cd": "devops",
            
            # Data/AI
            "machine learning": "data",
            "deep learning": "data",
            "tensorflow": "data",
            "pytorch": "data",
            "pandas": "data",
            "numpy": "data",
            "scikit-learn": "data",
            "analytics": "data",
            
            # Other
            "git": "tool",
            "jira": "tool",
            "agile": "methodology",
            "scrum": "methodology",
        }
        
        tags = []
        for row in rows:
            skill_lower = row.skill.lower()
            
            # Determine category
            category = "skill"  # default
            for key, cat in categories.items():
                if key in skill_lower:
                    category = cat
                    break
            
            tags.append({
                "name": row.skill,
                "count": row.count,
                "category": category
            })
        
        return tags


# Singleton instance
search_service = SearchService()