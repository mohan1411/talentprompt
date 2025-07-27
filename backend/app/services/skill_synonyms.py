"""Skill synonym expansion service for improved search matching."""

from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)


class SkillSynonymService:
    """Handle skill synonyms, abbreviations, and variations."""
    
    def __init__(self):
        # Technology abbreviations and expansions
        self.abbreviations = {
            # Programming Languages
            "js": ["javascript", "js"],
            "ts": ["typescript", "ts"],
            "py": ["python", "py"],
            "cpp": ["c++", "cpp", "cplusplus"],
            "cs": ["c#", "csharp", "cs", "c sharp"],
            "rb": ["ruby", "rb"],
            "go": ["golang", "go"],
            
            # Frameworks & Libraries
            "rn": ["react native", "rn", "reactnative"],
            "vue": ["vuejs", "vue", "vue.js"],
            "ng": ["angular", "ng", "angularjs"],
            
            # AI/ML
            "ml": ["machine learning", "ml"],
            "dl": ["deep learning", "dl"],
            "nlp": ["natural language processing", "nlp"],
            "cv": ["computer vision", "cv"],
            "ai": ["artificial intelligence", "ai"],
            "llm": ["large language model", "llm", "large language models"],
            "rl": ["reinforcement learning", "rl"],
            
            # DevOps & Cloud
            "k8s": ["kubernetes", "k8s"],
            "aws": ["amazon web services", "aws"],
            "gcp": ["google cloud platform", "gcp", "google cloud"],
            "ci/cd": ["continuous integration", "continuous deployment", "ci/cd", "cicd"],
            "iac": ["infrastructure as code", "iac"],
            
            # Databases
            "pg": ["postgresql", "postgres", "pg"],
            "mongo": ["mongodb", "mongo"],
            "redis": ["redis", "redis cache"],
            "es": ["elasticsearch", "es", "elastic search"],
            "ddb": ["dynamodb", "ddb", "dynamo"],
            
            # Other Tech
            "api": ["application programming interface", "api"],
            "ui": ["user interface", "ui"],
            "ux": ["user experience", "ux"],
            "qa": ["quality assurance", "qa", "testing"],
            "be": ["backend", "back-end", "be", "server-side"],
            "fe": ["frontend", "front-end", "fe", "client-side"],
            "fs": ["fullstack", "full-stack", "fs", "full stack"],
            "dsa": ["data structures and algorithms", "dsa", "algorithms"],
            "oop": ["object oriented programming", "oop", "object-oriented"],
            "tdd": ["test driven development", "tdd", "test-driven"],
            "bdd": ["behavior driven development", "bdd", "behavior-driven"],
            "ddd": ["domain driven design", "ddd", "domain-driven"],
            "mvc": ["model view controller", "mvc", "model-view-controller"],
            "mvvm": ["model view viewmodel", "mvvm", "model-view-viewmodel"],
            "rest": ["representational state transfer", "rest", "restful"],
            "grpc": ["grpc", "google remote procedure call"],
            "graphql": ["graphql", "graph ql"],
            "sql": ["structured query language", "sql"],
            "nosql": ["nosql", "no-sql", "non-relational"],
            "etl": ["extract transform load", "etl"],
            "elt": ["extract load transform", "elt"],
            "bi": ["business intelligence", "bi"],
            "erp": ["enterprise resource planning", "erp"],
            "crm": ["customer relationship management", "crm"],
            "cms": ["content management system", "cms"],
            "seo": ["search engine optimization", "seo"],
            "sem": ["search engine marketing", "sem"],
            "ppc": ["pay per click", "ppc"],
            "kpi": ["key performance indicator", "kpi"],
            "roi": ["return on investment", "roi"],
            "b2b": ["business to business", "b2b"],
            "b2c": ["business to consumer", "b2c"],
            "saas": ["software as a service", "saas"],
            "paas": ["platform as a service", "paas"],
            "iaas": ["infrastructure as a service", "iaas"],
        }
        
        # Technology synonyms and related terms
        self.synonyms = {
            # Programming paradigms
            "developer": ["engineer", "programmer", "coder", "software engineer"],
            "senior": ["sr", "lead", "principal", "staff", "senior-level"],
            "junior": ["jr", "entry-level", "associate", "junior-level"],
            "architect": ["architecture", "principal engineer", "staff engineer"],
            
            # Roles
            "devops": ["site reliability", "sre", "infrastructure", "platform engineer"],
            "fullstack": ["full-stack", "full stack", "generalist"],
            "backend": ["back-end", "server-side", "api developer"],
            "frontend": ["front-end", "client-side", "ui developer"],
            "mobile": ["ios", "android", "mobile app", "native app"],
            "data engineer": ["data pipeline", "etl developer", "data architect"],
            "data scientist": ["ml engineer", "machine learning engineer", "ai engineer"],
            "data analyst": ["business analyst", "bi analyst", "analytics"],
            
            # Skills groups
            "react": ["reactjs", "react.js", "react js"],
            "node": ["nodejs", "node.js", "node js"],
            "angular": ["angularjs", "angular.js", "angular js"],
            "vue": ["vuejs", "vue.js", "vue js"],
            "docker": ["containerization", "containers"],
            "testing": ["test", "qa", "quality assurance", "test automation"],
            "agile": ["scrum", "kanban", "agile methodology"],
            "cloud": ["cloud computing", "cloud infrastructure", "cloud services"],
            
            # Databases
            "database": ["db", "data storage", "persistence"],
            "sql": ["relational database", "rdbms"],
            "nosql": ["non-relational", "document database", "key-value store"],
            
            # Soft skills
            "leadership": ["team lead", "management", "mentoring"],
            "communication": ["communicator", "presentation", "interpersonal"],
            "problem solving": ["analytical", "troubleshooting", "critical thinking"],
        }
        
        # Build reverse mappings for efficient lookup
        self._build_reverse_mappings()
    
    def _build_reverse_mappings(self):
        """Build reverse mappings for efficient synonym lookup."""
        self.abbrev_to_expanded = {}
        self.expanded_to_abbrev = {}
        
        # Build abbreviation mappings
        for abbrev, expansions in self.abbreviations.items():
            self.abbrev_to_expanded[abbrev.lower()] = expansions
            for expansion in expansions:
                if expansion.lower() not in self.expanded_to_abbrev:
                    self.expanded_to_abbrev[expansion.lower()] = []
                self.expanded_to_abbrev[expansion.lower()].append(abbrev.lower())
        
        # Build synonym mappings
        self.synonym_groups = {}
        for primary, alternatives in self.synonyms.items():
            group = set([primary.lower()] + [alt.lower() for alt in alternatives])
            for term in group:
                self.synonym_groups[term] = group
    
    def expand_term(self, term: str) -> Set[str]:
        """
        Expand a single term to include all synonyms and variations.
        
        Args:
            term: The term to expand
            
        Returns:
            Set of all variations including the original term
        """
        term_lower = term.lower().strip()
        variations = {term_lower}
        
        # Check if it's an abbreviation
        if term_lower in self.abbrev_to_expanded:
            variations.update(self.abbrev_to_expanded[term_lower])
        
        # Check if it's an expanded form
        if term_lower in self.expanded_to_abbrev:
            variations.update(self.expanded_to_abbrev[term_lower])
        
        # Check for synonyms
        if term_lower in self.synonym_groups:
            variations.update(self.synonym_groups[term_lower])
        
        # Handle compound terms (e.g., "machine learning engineer")
        words = term_lower.split()
        if len(words) > 1:
            # Try expanding each word
            expanded_words = []
            for word in words:
                word_variations = self.expand_term(word)
                expanded_words.append(list(word_variations))
            
            # Don't create too many combinations
            if len(expanded_words) <= 3:
                from itertools import product
                for combo in product(*expanded_words):
                    variations.add(" ".join(combo))
        
        return variations
    
    def expand_query(self, query: str) -> List[str]:
        """
        Expand a search query to include synonyms and variations.
        
        Args:
            query: The search query
            
        Returns:
            List of query variations
        """
        # Split query into terms (simple tokenization)
        import re
        terms = re.findall(r'\b\w+(?:\.\w+)?(?:/\w+)?\b', query.lower())
        
        # Expand each term
        all_variations = set()
        all_variations.add(query.lower())
        
        for term in terms:
            term_variations = self.expand_term(term)
            if len(term_variations) > 1:
                # Add variations of the full query with term substitutions
                for variation in term_variations:
                    if variation != term:
                        query_variation = re.sub(
                            r'\b' + re.escape(term) + r'\b',
                            variation,
                            query.lower()
                        )
                        all_variations.add(query_variation)
        
        return list(all_variations)
    
    def get_related_skills(self, skill: str) -> List[str]:
        """
        Get skills related to the given skill.
        
        Args:
            skill: The skill to find related skills for
            
        Returns:
            List of related skills
        """
        variations = self.expand_term(skill)
        return [v for v in variations if v != skill.lower()]
    
    def normalize_skill(self, skill: str) -> str:
        """
        Normalize a skill to its canonical form.
        
        Args:
            skill: The skill to normalize
            
        Returns:
            Normalized skill name
        """
        skill_lower = skill.lower().strip()
        
        # If it's an abbreviation, use the first expansion
        if skill_lower in self.abbrev_to_expanded:
            return self.abbrev_to_expanded[skill_lower][0]
        
        # If it's in a synonym group, use the primary term
        if skill_lower in self.synonym_groups:
            # Find the primary term (first in the original synonyms dict)
            for primary, alternatives in self.synonyms.items():
                if skill_lower == primary.lower() or skill_lower in [alt.lower() for alt in alternatives]:
                    return primary.lower()
        
        return skill_lower


# Singleton instance
skill_synonyms = SkillSynonymService()