"""Async query parser with AI-powered typo correction."""

import re
from typing import List, Dict, Set, Any
import logging

from app.services.query_parser import QueryParser
from app.services.ai_typo_corrector import ai_typo_corrector

logger = logging.getLogger(__name__)


class AsyncQueryParser(QueryParser):
    """Async version of QueryParser that uses AI for typo correction."""
    
    async def parse_query_async(self, query: str) -> Dict[str, Any]:
        """
        Parse a search query asynchronously with AI typo correction.
        
        Args:
            query: The search query string
            
        Returns:
            Dictionary with parsed components including AI corrections
        """
        # Convert to lowercase and normalize spaces
        query_lower = query.lower().strip()
        query_lower = re.sub(r'\s+', ' ', query_lower)
        
        # Keep original for comparison
        original_query = query
        
        # Apply AI typo correction
        correction_result = await ai_typo_corrector.correct_query(query_lower)
        corrected_query = correction_result["corrected"]
        
        # Use corrected query for parsing
        if corrected_query != query_lower:
            query_lower = corrected_query
            logger.info(f"AI corrected query: '{original_query}' → '{corrected_query}'")
        
        # Extract years of experience if mentioned
        experience_years = self._extract_years(query_lower)
        if experience_years:
            # Remove experience pattern from query
            query_lower = re.sub(r'\d+\+?\s*(?:years?|yrs?)', '', query_lower)
        
        # Extract all potential terms
        terms = self._extract_terms(query_lower)
        
        # Identify components
        skills = []
        seniority = None
        roles = []
        remaining = []
        
        # Process terms
        processed = set()
        
        # First pass: identify multi-word skills
        for skill in sorted(self.known_skills, key=len, reverse=True):
            if re.search(r'\b' + re.escape(skill) + r'\b', query_lower) and skill not in processed:
                skills.append(skill)
                for word in skill.split():
                    processed.add(word)
        
        # Second pass: process individual terms
        for term in terms:
            if term in processed or term in self.stop_words:
                continue
                
            # Check if it's a skill
            normalized = self.skill_aliases.get(term, term)
            if normalized in self.known_skills:
                if normalized not in skills:
                    skills.append(normalized)
            # Check if it's a seniority level
            elif term in self.seniority_levels:
                if not seniority:
                    seniority = term
            # Check if it's a role type
            elif term in self.role_types:
                if term not in roles:
                    roles.append(term)
            # Otherwise it's a remaining term
            else:
                remaining.append(term)
        
        # Deduplicate skills while preserving order
        seen = set()
        unique_skills = []
        for skill in skills:
            normalized = self.skill_aliases.get(skill, skill)
            if normalized not in seen:
                seen.add(normalized)
                unique_skills.append(normalized)
        
        # Identify primary skill
        primary_skill = None
        if unique_skills:
            for role in roles:
                for skill in unique_skills:
                    if skill in role.lower() or role.lower() in skill:
                        primary_skill = skill
                        break
                if primary_skill:
                    break
            
            if not primary_skill:
                primary_skill = unique_skills[0]
        
        result = {
            "skills": unique_skills,
            "primary_skill": primary_skill,
            "seniority": seniority,
            "roles": roles,
            "experience_years": experience_years,
            "remaining_terms": remaining,
            "original_query": original_query,
            "corrected_query": corrected_query if correction_result["has_corrections"] else None,
            "corrections": correction_result.get("corrections", []),
            "correction_confidence": correction_result.get("confidence", 1.0)
        }
        
        return result


# Singleton instance
async_query_parser = AsyncQueryParser()