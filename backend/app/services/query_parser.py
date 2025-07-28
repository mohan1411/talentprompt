"""Query parser for extracting skills and requirements from search queries."""

import re
from typing import List, Dict, Set, Any
import logging

logger = logging.getLogger(__name__)


class QueryParser:
    """Parse search queries to extract skills, roles, and other requirements."""
    
    def __init__(self):
        # Common skill keywords that should be recognized
        self.known_skills = {
            # Programming Languages
            "python", "java", "javascript", "js", "typescript", "ts", "go", "golang",
            "rust", "c++", "c#", "csharp", "ruby", "php", "swift", "kotlin", "scala",
            "r", "matlab", "perl", "objective-c", "dart", "elixir", "haskell",
            
            # Frontend
            "react", "reactjs", "react.js", "angular", "angularjs", "vue", "vuejs",
            "vue.js", "svelte", "nextjs", "next.js", "nuxt", "gatsby", "ember",
            "backbone", "jquery", "html", "html5", "css", "css3", "sass", "scss",
            "less", "tailwind", "bootstrap", "material-ui", "mui", "webpack",
            "redux", "mobx", "rxjs",
            
            # Backend
            "nodejs", "node.js", "node", "django", "flask", "fastapi", "rails",
            "rubyonrails", "ruby on rails", "express", "expressjs", "spring",
            "springboot", "spring boot", ".net", "dotnet", "laravel", "symfony",
            "nestjs", "nest.js", "gin", "echo", "fiber", "actix",
            
            # Databases
            "sql", "mysql", "postgresql", "postgres", "mongodb", "mongo", "redis",
            "elasticsearch", "elastic", "cassandra", "dynamodb", "firebase",
            "sqlite", "oracle", "mssql", "sqlserver", "sql server", "neo4j",
            "couchdb", "influxdb", "clickhouse",
            
            # Cloud & DevOps
            "aws", "amazon web services", "azure", "gcp", "google cloud",
            "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins",
            "circleci", "circle ci", "gitlab", "github actions", "travis",
            "cloudformation", "helm", "prometheus", "grafana", "datadog",
            "newrelic", "new relic", "splunk",
            
            # AI/ML
            "machine learning", "ml", "deep learning", "dl", "tensorflow",
            "pytorch", "keras", "scikit-learn", "sklearn", "pandas", "numpy",
            "opencv", "cv", "computer vision", "nlp", "natural language processing",
            "bert", "gpt", "transformers", "huggingface", "hugging face",
            
            # Mobile
            "ios", "android", "react native", "flutter", "xamarin", "ionic",
            "swiftui", "kotlin multiplatform", "cordova", "phonegap",
            
            # Other Technologies
            "git", "graphql", "rest", "restful", "api", "microservices",
            "kafka", "rabbitmq", "redis", "elasticsearch", "nginx", "apache",
            "linux", "unix", "bash", "powershell", "vim", "emacs",
            "agile", "scrum", "kanban", "jira", "confluence", "slack",
            "ci/cd", "cicd", "devops", "sre", "devsecops"
        }
        
        # Normalize skill names
        self.skill_aliases = {
            "js": "javascript",
            "ts": "typescript",
            "golang": "go",
            "c#": "csharp",
            "react.js": "react",
            "vue.js": "vue",
            "node.js": "nodejs",
            "next.js": "nextjs",
            ".net": "dotnet",
            "rubyonrails": "ruby on rails",
            "k8s": "kubernetes",
            "ml": "machine learning",
            "dl": "deep learning",
            "cv": "computer vision",
            "nlp": "natural language processing",
            "ci/cd": "cicd"
        }
        
        # Seniority levels
        self.seniority_levels = {
            "junior", "jr", "entry", "entry-level", "graduate", "intern",
            "mid", "mid-level", "intermediate",
            "senior", "sr", "lead", "principal", "staff", "architect",
            "manager", "director", "vp", "cto", "head"
        }
        
        # Role types
        self.role_types = {
            "developer", "engineer", "programmer", "coder",
            "architect", "consultant", "analyst", "scientist",
            "administrator", "admin", "specialist", "expert",
            "manager", "lead", "coordinator", "designer"
        }
        
        # Common connecting words to filter out
        self.stop_words = {
            "with", "and", "or", "for", "in", "at", "on", "the", "a", "an",
            "to", "of", "by", "as", "is", "are", "was", "were", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "should", "could", "may", "might", "must", "can", "need",
            "experience", "years", "year", "looking", "seeking", "required"
        }
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse a search query to extract skills, seniority, and role information.
        
        Args:
            query: The search query string
            
        Returns:
            Dictionary with parsed components:
            - skills: List of identified skills
            - seniority: Detected seniority level (if any)
            - role: Detected role type (if any)
            - experience_years: Extracted years of experience (if mentioned)
            - remaining_terms: Terms that weren't categorized
        """
        # Import fuzzy matcher for typo correction
        from app.services.fuzzy_matcher import fuzzy_matcher
        
        # Convert to lowercase and normalize spaces
        query_lower = query.lower().strip()
        query_lower = re.sub(r'\s+', ' ', query_lower)
        
        # Keep original for comparison
        original_query_lower = query_lower
        
        # Apply typo correction
        corrected_query = fuzzy_matcher.correct_query(query_lower)
        if corrected_query != query_lower:
            query_lower = corrected_query
        
        # Extract years of experience if mentioned
        experience_years = self._extract_years(query_lower)
        if experience_years:
            # Remove experience pattern from query
            query_lower = re.sub(r'\d+\+?\s*(?:years?|yrs?)', '', query_lower)
        
        # Extract all potential terms
        # Split by common delimiters but keep multi-word skills
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
            # Use word boundary matching to prevent substring matches
            # This prevents 'r' from matching inside 'Developer'
            if re.search(r'\b' + re.escape(skill) + r'\b', query_lower) and skill not in processed:
                skills.append(skill)
                # Mark all words in this skill as processed
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
                if not seniority:  # Take first seniority found
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
        
        # Identify primary skill - usually the first skill mentioned or the one in the role
        primary_skill = None
        if unique_skills:
            # Check if any skill appears in the role description
            for role in roles:
                for skill in unique_skills:
                    if skill in role.lower() or role.lower() in skill:
                        primary_skill = skill
                        break
                if primary_skill:
                    break
            
            # If no skill in role, the first mentioned skill is primary
            if not primary_skill:
                primary_skill = unique_skills[0]
        
        result = {
            "skills": unique_skills,
            "primary_skill": primary_skill,
            "seniority": seniority,
            "roles": roles,
            "experience_years": experience_years,
            "remaining_terms": remaining,
            "original_query": query,
            "corrected_query": corrected_query if corrected_query != original_query_lower else None
        }
        
        
        return result
    
    def _extract_years(self, query: str) -> int:
        """Extract years of experience from query."""
        # Match patterns like "5+ years", "10 years", "3-5 years"
        patterns = [
            r'(\d+)\+\s*(?:years?|yrs?)',  # 5+ years
            r'(\d+)\s*(?:years?|yrs?)',     # 5 years
            r'(\d+)-\d+\s*(?:years?|yrs?)', # 3-5 years (take lower bound)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_terms(self, query: str) -> List[str]:
        """Extract individual terms from query."""
        # Replace common punctuation with spaces
        query = re.sub(r'[,;:]', ' ', query)
        
        # Split into words
        words = query.split()
        
        # Clean up each word
        terms = []
        for word in words:
            # Remove trailing punctuation
            word = word.strip('.,!?')
            if word:
                terms.append(word)
        
        return terms
    
    def extract_skill_requirements(self, query: str) -> List[str]:
        """
        Extract just the skill requirements from a query.
        This is a convenience method for search scoring.
        
        Args:
            query: The search query
            
        Returns:
            List of required skills
        """
        parsed = self.parse_query(query)
        return parsed["skills"]
    
    def is_skill_query(self, query: str) -> bool:
        """
        Determine if a query is primarily skill-focused.
        
        Args:
            query: The search query
            
        Returns:
            True if the query contains identifiable skills
        """
        parsed = self.parse_query(query)
        return len(parsed["skills"]) > 0


# Singleton instance
query_parser = QueryParser()