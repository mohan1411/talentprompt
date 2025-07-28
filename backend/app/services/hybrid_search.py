"""Hybrid search service combining keyword and vector search with BM25 algorithm."""

import math
import logging
from typing import List, Dict, Any, Tuple, Optional, Set
from collections import Counter
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_, or_
import sqlalchemy as sa
from app.models.resume import Resume
from app.services.skill_synonyms import skill_synonyms
from app.services.vector_search import vector_search
from app.services.fuzzy_matcher import fuzzy_matcher

logger = logging.getLogger(__name__)


class HybridSearchService:
    """Combine keyword search (BM25) with vector search for improved results."""
    
    def __init__(self):
        # BM25 parameters
        self.k1 = 1.2  # Term frequency saturation parameter
        self.b = 0.75  # Length normalization parameter
        
        # Hybrid weighting
        self.keyword_weight = 0.3
        self.vector_weight = 0.7
        
    async def search(
        self,
        db: AsyncSession,
        query: str,
        user_id: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        use_synonyms: bool = True
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform hybrid search combining BM25 keyword search and vector search.
        
        Args:
            db: Database session
            query: Search query
            user_id: User ID for filtering
            limit: Maximum results to return
            filters: Additional filters
            use_synonyms: Whether to expand query with synonyms
            
        Returns:
            List of (resume_data, score) tuples
        """
        # Expand query with synonyms if enabled
        expanded_queries = [query]
        if use_synonyms:
            expanded_queries.extend(skill_synonyms.expand_query(query))
            logger.info(f"Expanded query from '{query}' to {len(expanded_queries)} variations")
        
        # Perform both searches in parallel
        keyword_results = await self._keyword_search_bm25(
            db, expanded_queries, user_id, limit * 2, filters
        )
        
        vector_results = await vector_search.search_similar(
            query, user_id, limit * 2, filters
        )
        
        # Combine and re-rank results
        combined_results = self._combine_results(
            keyword_results, vector_results, limit
        )
        
        return combined_results
    
    async def _keyword_search_bm25(
        self,
        db: AsyncSession,
        queries: List[str],
        user_id: str,
        limit: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform BM25-based keyword search using PostgreSQL full-text search.
        
        Args:
            db: Database session
            queries: List of query variations
            user_id: User ID for filtering
            limit: Maximum results
            filters: Additional filters
            
        Returns:
            List of (resume_data, score) tuples with BM25 scores
        """
        # Tokenize and prepare queries
        all_terms = set()
        for query in queries:
            terms = self._tokenize_query(query)
            all_terms.update(terms)
        
        # Build search conditions
        conditions = [Resume.user_id == user_id]
        
        # Add text search conditions with fuzzy matching support
        text_conditions = []
        for term in all_terms:
            # Search in multiple fields
            term_lower = term.lower()
            
            # Create conditions for exact term match
            # Use actual columns that exist in the model
            conditions_list = []
            
            # Add condition for raw_text if it exists
            conditions_list.append(
                func.lower(func.coalesce(Resume.raw_text, '')).contains(term_lower)
            )
            
            # Add condition for summary
            conditions_list.append(
                func.lower(func.coalesce(Resume.summary, '')).contains(term_lower)
            )
            
            # Add condition for current_title
            conditions_list.append(
                func.lower(func.coalesce(Resume.current_title, '')).contains(term_lower)
            )
            
            # Add condition for skills JSON array
            # Convert JSON array to text for searching
            conditions_list.append(
                func.lower(func.coalesce(func.cast(Resume.skills, sa.Text), '')).contains(term_lower)
            )
            
            exact_conditions = or_(*conditions_list)
            
            # Add fuzzy match conditions for skills
            # Note: This is simplified - in production, you'd want to use PostgreSQL's fuzzy search
            fuzzy_conditions = []
            
            # Check for common typos/variations
            corrections = fuzzy_matcher.suggest_corrections([term])
            if term in corrections:
                corrected = corrections[term].lower()
                fuzzy_conditions.append(
                    or_(
                        func.lower(func.coalesce(Resume.raw_text, '')).contains(corrected),
                        func.lower(func.coalesce(func.cast(Resume.skills, sa.Text), '')).contains(corrected)
                    )
                )
            
            # Combine exact and fuzzy conditions
            if fuzzy_conditions:
                text_conditions.append(or_(exact_conditions, *fuzzy_conditions))
            else:
                text_conditions.append(exact_conditions)
        
        if text_conditions:
            conditions.append(or_(*text_conditions))
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(Resume, key):
                    conditions.append(getattr(Resume, key) == value)
        
        # Execute search
        query_obj = select(Resume).where(and_(*conditions)).limit(limit)
        result = await db.execute(query_obj)
        resumes = result.scalars().all()
        
        # Calculate BM25 scores
        scored_results = []
        
        # Get document statistics for BM25
        doc_count = await self._get_document_count(db, user_id)
        avg_doc_length = await self._get_avg_document_length(db, user_id)
        
        for resume in resumes:
            # Calculate BM25 score
            score = self._calculate_bm25_score(
                resume, all_terms, doc_count, avg_doc_length
            )
            
            resume_dict = {
                "id": str(resume.id),
                "first_name": resume.first_name,
                "last_name": resume.last_name,
                "email": resume.email,
                "location": resume.location,
                "current_title": resume.current_title,
                "years_experience": resume.years_experience,
                "skills": resume.skills or [],
                "summary": resume.summary,
                "score": score
            }
            
            scored_results.append((resume_dict, score))
        
        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return scored_results[:limit]
    
    def _tokenize_query(self, query: str) -> List[str]:
        """Tokenize query into searchable terms."""
        # Simple tokenization - can be enhanced
        tokens = re.findall(r'\b\w+\b', query.lower())
        
        # Expand abbreviations
        expanded_tokens = []
        for token in tokens:
            expanded_tokens.append(token)
            # Add expanded forms
            variations = skill_synonyms.expand_term(token)
            if len(variations) > 1:
                expanded_tokens.extend(variations - {token})
        
        return list(set(expanded_tokens))
    
    def _calculate_bm25_score(
        self,
        resume: Resume,
        terms: Set[str],
        doc_count: int,
        avg_doc_length: float
    ) -> float:
        """
        Calculate BM25 score for a resume given search terms.
        
        BM25 formula:
        score = Σ IDF(term) * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl/avgdl))
        
        Where:
        - IDF = log((N - df + 0.5) / (df + 0.5))
        - tf = term frequency in document
        - dl = document length
        - avgdl = average document length
        - N = total number of documents
        - df = document frequency (docs containing term)
        """
        # Combine all searchable text from actual columns
        skills_text = " ".join(resume.skills) if resume.skills else ""
        doc_text = " ".join(filter(None, [
            resume.raw_text or "",
            resume.summary or "",
            skills_text,
            resume.current_title or ""
        ])).lower()
        
        # Calculate document length
        doc_length = len(doc_text.split())
        if doc_length == 0:
            return 0.0
        
        score = 0.0
        
        for term in terms:
            # Term frequency
            tf = doc_text.count(term.lower())
            if tf == 0:
                continue
            
            # For now, assume df = N/10 (can be improved with actual counts)
            # This is a simplification - in production, we'd query actual document frequencies
            df = max(1, doc_count / 10)
            
            # IDF calculation
            idf = math.log((doc_count - df + 0.5) / (df + 0.5))
            
            # BM25 term score
            term_score = idf * (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * doc_length / avg_doc_length)
            )
            
            score += term_score
        
        return score
    
    async def _get_document_count(self, db: AsyncSession, user_id: str) -> int:
        """Get total document count for user."""
        result = await db.execute(
            select(func.count(Resume.id)).where(Resume.user_id == user_id)
        )
        return result.scalar() or 1
    
    async def _get_avg_document_length(self, db: AsyncSession, user_id: str) -> float:
        """Get average document length for BM25 normalization."""
        # For simplicity, return a constant. In production, calculate actual average
        return 500.0
    
    def _combine_results(
        self,
        keyword_results: List[Tuple[Dict[str, Any], float]],
        vector_results: List[Dict[str, Any]],
        limit: int
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Combine keyword and vector search results using weighted scoring.
        
        Args:
            keyword_results: Results from BM25 keyword search
            vector_results: Results from vector search
            limit: Maximum results to return
            
        Returns:
            Combined and re-ranked results
        """
        # Create score maps
        keyword_scores = {r[0]["id"]: r[1] for r in keyword_results}
        vector_scores = {r["resume_id"]: r["score"] for r in vector_results}
        
        # Normalize scores to 0-1 range
        keyword_max = max(keyword_scores.values()) if keyword_scores else 1.0
        vector_max = max(vector_scores.values()) if vector_scores else 1.0
        
        # Combine all unique IDs
        all_ids = set(keyword_scores.keys()) | set(vector_scores.keys())
        
        # Calculate hybrid scores
        hybrid_results = []
        
        for resume_id in all_ids:
            # Get normalized scores
            keyword_score = keyword_scores.get(resume_id, 0) / keyword_max
            vector_score = vector_scores.get(resume_id, 0) / vector_max
            
            # Calculate weighted hybrid score
            hybrid_score = (
                self.keyword_weight * keyword_score +
                self.vector_weight * vector_score
            )
            
            # Get resume data (prefer from keyword results as they have full data)
            resume_data = None
            for r in keyword_results:
                if r[0]["id"] == resume_id:
                    resume_data = r[0]
                    break
            
            if not resume_data:
                # Get from vector results
                for r in vector_results:
                    if r["resume_id"] == resume_id:
                        resume_data = r.get("metadata", {})
                        resume_data["id"] = resume_id
                        break
            
            if resume_data:
                resume_data["hybrid_score"] = hybrid_score
                resume_data["keyword_score"] = keyword_score
                resume_data["vector_score"] = vector_score
                hybrid_results.append((resume_data, hybrid_score))
        
        # Sort by hybrid score
        hybrid_results.sort(key=lambda x: x[1], reverse=True)
        
        return hybrid_results[:limit]
    
    def adjust_weights(self, query_type: str):
        """
        Adjust keyword/vector weights based on query type.
        
        Args:
            query_type: Type of query (technical, soft_skills, experience, etc.)
        """
        if query_type == "technical":
            # Technical queries benefit more from keyword matching
            self.keyword_weight = 0.4
            self.vector_weight = 0.6
        elif query_type == "soft_skills":
            # Soft skills benefit more from semantic understanding
            self.keyword_weight = 0.2
            self.vector_weight = 0.8
        elif query_type == "exact_match":
            # Exact matches should heavily favor keywords
            self.keyword_weight = 0.7
            self.vector_weight = 0.3
        else:
            # Default balanced weights
            self.keyword_weight = 0.3
            self.vector_weight = 0.7


# Singleton instance
hybrid_search = HybridSearchService()