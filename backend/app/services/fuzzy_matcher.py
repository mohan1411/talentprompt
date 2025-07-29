"""Fuzzy matching service for skill comparison and typo tolerance."""

import logging
from typing import List, Tuple, Optional, Set
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)


class FuzzyMatcher:
    """Handle fuzzy matching for skills and other text comparisons."""
    
    def __init__(self, threshold: float = 0.75):
        """
        Initialize fuzzy matcher.
        
        Args:
            threshold: Minimum similarity score (0-1) to consider a match
        """
        self.threshold = threshold
        
        # Common typos and variations
        self.common_replacements = {
            "javascript": ["javscript", "javascirpt", "javascrpt", "javasript", "javascipt"],
            "python": ["pyton", "pythoon", "pythn", "pythonn", "pythno", "phyton", "pyhton"],
            "kubernetes": ["kubernets", "kuberentes", "k8", "kubenetes", "kubernates"],
            "postgresql": ["postgre", "postgres", "postgress", "postgressql", "psql"],
            "mongodb": ["mongo", "mangodb", "mongoddb", "monogdb"],
            "react": ["reactjs", "react.js", "reatc", "raect"],
            "angular": ["angularjs", "angular.js", "angluar", "anguler"],
            "vue": ["vuejs", "vue.js", "veu", "vuee"],
            "node": ["nodejs", "node.js", "nodjs", "noed"],
            "typescript": ["typscript", "typescirpt", "ts", "typescipt", "tyepscript"],
            "docker": ["dokcer", "dcoker", "doker", "dockr"],
            "jenkins": ["jenkis", "jenkin", "jenkinss", "jenkings"],
            "terraform": ["teraform", "terrafrom", "terrafom", "terrafrm"],
            "elasticsearch": ["elastic", "elasticsearh", "elastisearch", "elsaticsearch"],
            "redis": ["reddis", "rediss", "ridis", "radis"],
            "aws": ["ams", "awz", "aws", "amason web services"]
        }
        
        # Build reverse mapping
        self.typo_corrections = {}
        for correct, typos in self.common_replacements.items():
            for typo in typos:
                self.typo_corrections[typo.lower()] = correct
    
    def similarity_score(self, str1: str, str2: str) -> float:
        """
        Calculate similarity score between two strings.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        # Normalize strings
        str1 = self._normalize(str1)
        str2 = self._normalize(str2)
        
        # Exact match
        if str1 == str2:
            return 1.0
        
        # Check for typo corrections
        corrected1 = self.typo_corrections.get(str1, str1)
        corrected2 = self.typo_corrections.get(str2, str2)
        
        if corrected1 == corrected2:
            return 0.95  # High score for known typos
        
        # Calculate base similarity
        ratio = SequenceMatcher(None, str1, str2).ratio()
        
        # Boost score for common patterns
        if self._has_common_pattern(str1, str2):
            ratio = min(1.0, ratio * 1.1)
        
        return ratio
    
    def fuzzy_match(self, query: str, candidates: List[str]) -> List[Tuple[str, float]]:
        """
        Find fuzzy matches for a query string in a list of candidates.
        
        Args:
            query: The string to match
            candidates: List of candidate strings
            
        Returns:
            List of (candidate, score) tuples sorted by score
        """
        matches = []
        query_normalized = self._normalize(query)
        
        for candidate in candidates:
            score = self.similarity_score(query, candidate)
            if score >= self.threshold:
                matches.append((candidate, score))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def find_best_match(self, query: str, candidates: List[str]) -> Optional[str]:
        """
        Find the best matching candidate for a query.
        
        Args:
            query: The string to match
            candidates: List of candidate strings
            
        Returns:
            Best matching candidate or None if no good match
        """
        matches = self.fuzzy_match(query, candidates)
        return matches[0][0] if matches else None
    
    def match_skills(
        self, 
        query_skills: List[str], 
        candidate_skills: List[str],
        exact_only: bool = False
    ) -> Tuple[List[str], List[str], float]:
        """
        Match skills between query and candidate with fuzzy matching.
        
        Args:
            query_skills: Skills from the search query
            candidate_skills: Skills from the candidate
            exact_only: If True, only exact matches count
            
        Returns:
            Tuple of (matched_skills, missing_skills, match_score)
        """
        matched = []
        missing = []
        
        # Normalize all skills
        candidate_normalized = {self._normalize(s): s for s in candidate_skills}
        
        for query_skill in query_skills:
            if exact_only:
                # Exact match only
                query_norm = self._normalize(query_skill)
                if query_norm in candidate_normalized:
                    matched.append(query_skill)
                else:
                    missing.append(query_skill)
            else:
                # Fuzzy match
                best_match = None
                best_score = 0.0
                
                for cand_norm, cand_original in candidate_normalized.items():
                    score = self.similarity_score(query_skill, cand_original)
                    if score > best_score and score >= self.threshold:
                        best_score = score
                        best_match = query_skill
                
                if best_match:
                    matched.append(best_match)
                else:
                    missing.append(query_skill)
        
        # Calculate match score
        if query_skills:
            match_score = len(matched) / len(query_skills)
        else:
            match_score = 0.0
        
        return matched, missing, match_score
    
    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove special characters but keep spaces, dots, and dashes
        text = re.sub(r'[^a-z0-9\s\.\-]', '', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _has_common_pattern(self, str1: str, str2: str) -> bool:
        """Check if strings share common patterns."""
        patterns = [
            # One is abbreviation of the other
            (str1.startswith(str2[:3]) or str2.startswith(str1[:3])) and abs(len(str1) - len(str2)) > 3,
            # Common suffixes
            (str1.endswith("js") and str2.endswith("script")) or (str2.endswith("js") and str1.endswith("script")),
            (str1.endswith("db") and "database" in str2) or (str2.endswith("db") and "database" in str1),
            # Version numbers
            re.search(r'\d+', str1) and re.search(r'\d+', str2) and str1.replace(re.search(r'\d+', str1).group(), '') == str2.replace(re.search(r'\d+', str2).group(), '')
        ]
        
        return any(patterns)
    
    def suggest_corrections(self, terms: List[str]) -> dict:
        """
        Suggest corrections for potentially misspelled terms.
        
        Args:
            terms: List of terms to check
            
        Returns:
            Dictionary of {term: suggested_correction} for likely typos
        """
        suggestions = {}
        
        # Also check against common programming terms
        common_tech_terms = [
            "python", "javascript", "java", "react", "angular", "vue", "node",
            "docker", "kubernetes", "aws", "azure", "gcp", "typescript",
            "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
            "django", "flask", "spring", "express", "rails", "laravel",
            "mysql", "postgresql", "mongodb", "redis", "elasticsearch"
        ]
        
        for term in terms:
            term_lower = self._normalize(term)
            
            # Check direct typo mapping
            if term_lower in self.typo_corrections:
                suggestions[term] = self.typo_corrections[term_lower]
                continue
            
            # Check against all known correct terms plus common tech terms
            all_correct_terms = list(set(list(self.common_replacements.keys()) + common_tech_terms))
            matches = self.fuzzy_match(term, all_correct_terms)
            
            if matches and matches[0][1] >= 0.80:  # Slightly lower threshold for dynamic matching
                suggestions[term] = matches[0][0]
        
        return suggestions
    
    def correct_query(self, query: str) -> str:
        """
        Correct typos in a query string using manual dictionary.
        For AI-powered correction, use ai_typo_corrector.
        
        Args:
            query: The query string to correct
            
        Returns:
            Corrected query string
        """
        words = query.split()
        corrections = self.suggest_corrections(words)
        
        corrected_words = []
        for word in words:
            # Check both original case and lowercase
            word_lower = word.lower()
            if word in corrections:
                corrected_words.append(corrections[word])
            elif word_lower in corrections:
                corrected_words.append(corrections[word_lower])
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)


# Singleton instance
fuzzy_matcher = FuzzyMatcher()