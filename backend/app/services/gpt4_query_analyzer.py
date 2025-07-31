"""GPT-4.1-mini powered query analyzer for advanced search understanding."""

import logging
import json
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI

from app.core.config import settings
from app.services.query_parser import query_parser

logger = logging.getLogger(__name__)


class GPT4QueryAnalyzer:
    """
    Advanced query analyzer using GPT-4.1-mini for superior understanding of:
    - Complex natural language queries
    - Implicit requirements
    - Industry-specific terminology
    - Multi-dimensional search intent
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = settings.OPENAI_MODEL  # gpt-4.1-mini-2025-04-14
        
    async def analyze_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a search query using GPT-4.1-mini for deep understanding.
        
        Args:
            query: The search query
            context: Optional context (previous searches, user preferences)
            
        Returns:
            Comprehensive query analysis
        """
        logger.info(f"[GPT4] analyze_query called with: '{query}'")
        
        # Start with basic parsing
        basic_parse = query_parser.parse_query(query)
        logger.info(f"[GPT4] basic_parse skills: {basic_parse.get('skills', [])}")
        
        # CRITICAL: If the query has been corrected, ensure we have the corrected version in basic_parse
        if " " in query and not basic_parse.get("skills"):
            # Try parsing individual words to catch corrected skills
            words = query.lower().split()
            for word in words:
                if word in query_parser.known_skills:
                    if "skills" not in basic_parse:
                        basic_parse["skills"] = []
                    if word not in [s.lower() for s in basic_parse["skills"]]:
                        basic_parse["skills"].append(word)
            logger.info(f"[GPT4] Re-extracted skills from query words: {basic_parse.get('skills', [])}")
        
        # If no OpenAI key, return enhanced basic parse
        if not self.client:
            logger.info("[GPT4] No OpenAI client, using enhanced basic parse")
            enhanced = self._enhance_basic_parse(basic_parse)
            logger.info(f"[GPT4] Enhanced parse - secondary_skills: {enhanced.get('secondary_skills', [])}")
            return enhanced
        
        try:
            # Prepare the prompt for GPT-4.1-mini
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(query, context)
            
            # Call GPT-4.1-mini
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            gpt_analysis = json.loads(response.choices[0].message.content)
            
            # Merge with basic parse
            enhanced_analysis = self._merge_analyses(basic_parse, gpt_analysis)
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"Error in GPT-4.1-mini analysis: {e}")
            # Fallback to enhanced basic parse
            return self._enhance_basic_parse(basic_parse)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for GPT-4.1-mini."""
        return """You are an expert technical recruiter analyzing search queries for a resume database.
        
Your task is to deeply understand the search intent and extract ALL relevant information.

Analyze the query and return a JSON object with:
{
    "primary_skills": ["main technical skills required"],
    "secondary_skills": ["nice-to-have skills"],
    "implied_skills": ["skills not mentioned but typically required"],
    "experience_level": "junior/mid/senior/lead/any",
    "experience_years_min": null or number,
    "experience_years_max": null or number,
    "role_type": "frontend/backend/fullstack/devops/data/mobile/embedded/any",
    "industry_preference": ["industries if mentioned"],
    "soft_skills": ["leadership", "mentoring", etc if mentioned],
    "education_requirements": ["degree types if mentioned"],
    "certifications": ["specific certifications if mentioned"],
    "location_preferences": ["remote", "onsite", "hybrid", "specific locations"],
    "company_size_preference": "startup/midsize/enterprise/any",
    "special_requirements": ["security clearance", "visa status", etc],
    "search_intent": "exact_match/exploratory/skill_focused/role_focused",
    "query_type": "technical/soft_skills/experience/exact_match/exploratory",
    "query_quality": "high/medium/low",
    "suggested_expansions": ["alternative search terms"],
    "interpretation_notes": "brief explanation of query understanding"
}

Examples:
- "Senior Python Developer with AWS" implies: Python expertise, AWS skills, 5+ years experience, likely needs Docker, Linux, Git
- "Full-stack engineer for startup" implies: Frontend + Backend skills, adaptability, multiple technologies, comfortable with ambiguity
- "ML engineer with production experience" implies: Python/R, TensorFlow/PyTorch, MLOps, cloud platforms, data engineering skills

Be comprehensive but realistic. Don't over-interpret."""
    
    def _build_user_prompt(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Build the user prompt with query and context."""
        prompt = f"Analyze this recruitment search query: \"{query}\""
        
        if context:
            if context.get("previous_searches"):
                prompt += f"\n\nPrevious searches in this session: {', '.join(context['previous_searches'][-3:])}"
            
            if context.get("user_industry"):
                prompt += f"\n\nUser's industry: {context['user_industry']}"
            
            if context.get("typical_roles"):
                prompt += f"\n\nTypically hires for: {', '.join(context['typical_roles'])}"
        
        return prompt
    
    def _enhance_basic_parse(self, basic_parse: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance basic parse with rule-based logic when GPT-4.1-mini unavailable."""
        enhanced = basic_parse.copy()
        
        # IMPORTANT: If we have a corrected_query but empty skills, re-extract skills
        if enhanced.get("corrected_query") and not enhanced.get("skills"):
            corrected_words = enhanced["corrected_query"].lower().split()
            for word in corrected_words:
                if word in query_parser.known_skills:
                    if "skills" not in enhanced:
                        enhanced["skills"] = []
                    enhanced["skills"].append(word)
            logger.info(f"[GPT4] Re-extracted skills from corrected query: {enhanced.get('skills')}")
        
        # Add implied skills based on primary skills
        implied_skills = []
        # Define secondary skills (nice to have) for each primary skill
        # Using lowercase keys for case-insensitive matching
        secondary_skill_map = {
            "python": ["django", "flask", "fastapi", "pandas", "numpy"],
            "javascript": ["react", "node.js", "typescript", "vue", "angular"],
            "typescript": ["react", "node.js", "angular", "nestjs"],
            "react": ["redux", "next.js", "styled-components", "webpack"],
            "aws": ["docker", "terraform", "kubernetes", "lambda", "s3"],
            "docker": ["kubernetes", "docker-compose", "ci/cd", "jenkins"],
            "java": ["spring", "spring boot", "hibernate", "maven", "gradle"],
            "kubernetes": ["helm", "prometheus", "grafana", "istio"],
            "devops": ["terraform", "ansible", "jenkins", "gitlab ci"],
            "golang": ["microservices", "grpc", "docker", "kubernetes"],
            "go": ["microservices", "grpc", "docker", "kubernetes"],  # Alias for golang
            "rust": ["webassembly", "async", "tokio", "actix"],
            "nodejs": ["express", "nestjs", "mongodb", "postgresql"],
            "node.js": ["express", "nestjs", "mongodb", "postgresql"],  # Alternative spelling
            "node": ["express", "nestjs", "mongodb", "postgresql"],  # Short form
            "django": ["rest framework", "celery", "postgresql", "redis"],
            "rails": ["rspec", "sidekiq", "postgresql", "redis"],
            "c++": ["stl", "boost", "cmake", "qt", "opencv"],
            "c#": ["asp.net", "entity framework", "unity", "xamarin"],
            "csharp": ["asp.net", "entity framework", "unity", "xamarin"],  # Alternative spelling
            "php": ["laravel", "symfony", "wordpress", "composer"],
            "ruby": ["rails", "sinatra", "rspec", "sidekiq"],
            "swift": ["ios", "swiftui", "cocoapods", "xcode"],
            "kotlin": ["android", "spring boot", "gradle", "coroutines"],
            "scala": ["akka", "play", "spark", "sbt"],
            "vue": ["vuex", "nuxt.js", "vue router", "vuetify"],
            "angular": ["rxjs", "ngrx", "material", "ionic"],
            "flutter": ["dart", "firebase", "bloc", "provider"],
            "mongodb": ["mongoose", "aggregation", "atlas", "nosql"],
            "postgresql": ["pgadmin", "postgis", "replication", "optimization"],
            "mysql": ["mariadb", "replication", "optimization", "workbench"],
            "redis": ["caching", "pub/sub", "lua scripting", "cluster"],
            "elasticsearch": ["kibana", "logstash", "beats", "lucene"],
        }
        
        # Define implied skills (commonly needed but not mentioned)
        skill_implications = {
            "python": ["pip", "virtualenv", "debugging", "git"],
            "javascript": ["npm", "es6", "async/await", "git", "json"],
            "typescript": ["npm", "es6", "types", "git", "json"],
            "react": ["jsx", "state management", "hooks", "dom"],
            "aws": ["cloud", "linux", "networking", "security"],
            "docker": ["containers", "linux", "devops", "yaml"],
            "kubernetes": ["docker", "yaml", "helm", "cloud native"],
            "java": ["jvm", "maven", "gradle", "junit", "git"],
            "golang": ["modules", "goroutines", "channels", "git"],
            "go": ["modules", "goroutines", "channels", "git"],  # Alias
            "nodejs": ["npm", "async/await", "modules", "git"],
            "node.js": ["npm", "async/await", "modules", "git"],  # Alternative
            "node": ["npm", "async/await", "modules", "git"],  # Short form
            "machine learning": ["python", "statistics", "data analysis", "math"],
            "frontend": ["html", "css", "responsive design", "browser"],
            "backend": ["api", "database", "server", "rest"],
            "fullstack": ["frontend", "backend", "database", "deployment"],
            "c++": ["pointers", "memory management", "compilation", "git"],
            "c#": [".net", "visual studio", "nuget", "git"],
            "csharp": [".net", "visual studio", "nuget", "git"],  # Alternative
            "php": ["composer", "apache/nginx", "mysql", "git"],
            "ruby": ["gems", "bundler", "rake", "git"],
            "rust": ["cargo", "ownership", "memory safety", "git"]
        }
        
        # Collect secondary skills based on primary skills
        collected_secondary_skills = []
        logger.info(f"[GPT4] Skills from parsed_query: {enhanced.get('skills', [])}")
        logger.info(f"[GPT4] Original query: {enhanced.get('original_query')}")
        logger.info(f"[GPT4] Corrected query: {enhanced.get('corrected_query')}")
        
        # Ensure we have skills to work with
        skills_to_process = enhanced.get("skills", [])
        if not skills_to_process and enhanced.get("primary_skills"):
            skills_to_process = enhanced.get("primary_skills", [])
            logger.info(f"[GPT4] Using primary_skills instead: {skills_to_process}")
        
        for skill in skills_to_process:
            skill_lower = skill.lower()
            # Try exact match first
            if skill_lower in secondary_skill_map:
                collected_secondary_skills.extend(secondary_skill_map[skill_lower])
                logger.info(f"[GPT4] Found secondary skills for '{skill}': {secondary_skill_map[skill_lower]}")
            else:
                logger.info(f"[GPT4] No secondary skills found for '{skill}' (lowercased: '{skill_lower}')")
                # Log available keys for debugging
                similar_keys = [k for k in secondary_skill_map.keys() if k.startswith(skill_lower[:3])]
                if similar_keys:
                    logger.info(f"[GPT4] Similar keys in map: {similar_keys}")
            
            if skill_lower in skill_implications:
                implied_skills.extend(skill_implications[skill_lower])
        
        # Determine role type from skills and query
        role_type = self._determine_role_type(enhanced)
        
        # Estimate experience level
        experience_level = "any"
        if enhanced.get("seniority"):
            seniority_map = {
                "junior": "junior",
                "mid": "mid",
                "senior": "senior",
                "lead": "lead",
                "principal": "lead",
                "staff": "lead"
            }
            experience_level = seniority_map.get(enhanced["seniority"], "any")
        
        # Determine query type
        query_type = self._determine_query_type(enhanced)
        
        # Deduplicate skills before building enhanced analysis
        def dedupe_skills(skills_list):
            seen = {}
            result = []
            for skill in skills_list:
                skill_lower = skill.lower()
                if skill_lower not in seen:
                    seen[skill_lower] = skill
                    result.append(skill)
            return result
        
        # Get deduplicated skills
        all_skills = dedupe_skills(enhanced.get("skills", []))
        
        # Remove primary skills from secondary skills and deduplicate
        primary_skills_lower = [s.lower() for s in all_skills[:3]]
        secondary_skills_deduped = []
        seen_secondary = set()
        
        for skill in collected_secondary_skills:
            skill_lower = skill.lower()
            if skill_lower not in primary_skills_lower and skill_lower not in seen_secondary:
                secondary_skills_deduped.append(skill)
                seen_secondary.add(skill_lower)
        
        # Limit secondary skills to top 5
        secondary_skills = secondary_skills_deduped[:5]
        
        # Build enhanced analysis
        enhanced.update({
            "primary_skills": all_skills[:3],
            "secondary_skills": secondary_skills,
            "implied_skills": dedupe_skills(list(set(implied_skills) - set([s.lower() for s in all_skills]) - set([s.lower() for s in secondary_skills])))[:5],
            "experience_level": experience_level,
            "role_type": role_type,
            "search_intent": "skill_focused" if all_skills else "exploratory",
            "query_type": query_type,
            "query_quality": "high" if all_skills else "medium"
        })
        
        logger.info(f"[GPT4] Enhanced analysis - primary: {enhanced.get('primary_skills')}, secondary: {enhanced.get('secondary_skills')}, implied: {enhanced.get('implied_skills')}")
        
        return enhanced
    
    def _determine_role_type(self, parsed: Dict[str, Any]) -> str:
        """Determine role type from skills and keywords."""
        skills = [s.lower() for s in parsed.get("skills", [])]
        roles = [r.lower() for r in parsed.get("roles", [])]
        query_lower = parsed.get("original_query", "").lower()
        
        # Check for specific role indicators
        if any(term in query_lower for term in ["frontend", "front-end", "ui", "ux"]):
            return "frontend"
        elif any(term in query_lower for term in ["backend", "back-end", "server", "api"]):
            return "backend"
        elif any(term in query_lower for term in ["fullstack", "full-stack", "full stack"]):
            return "fullstack"
        elif any(term in query_lower for term in ["devops", "sre", "infrastructure"]):
            return "devops"
        elif any(term in query_lower for term in ["data", "analytics", "ml", "machine learning", "ai"]):
            return "data"
        elif any(term in query_lower for term in ["mobile", "ios", "android", "react native"]):
            return "mobile"
        
        # Infer from skills
        frontend_skills = {"react", "angular", "vue", "css", "html", "javascript", "typescript"}
        backend_skills = {"python", "java", "node", "django", "spring", "express", "database"}
        devops_skills = {"docker", "kubernetes", "aws", "terraform", "jenkins", "ci/cd"}
        data_skills = {"pandas", "numpy", "tensorflow", "pytorch", "sql", "spark"}
        
        skill_set = set(skills)
        
        if skill_set & frontend_skills and skill_set & backend_skills:
            return "fullstack"
        elif skill_set & frontend_skills:
            return "frontend"
        elif skill_set & backend_skills:
            return "backend"
        elif skill_set & devops_skills:
            return "devops"
        elif skill_set & data_skills:
            return "data"
        
        return "any"
    
    def _determine_query_type(self, parsed: Dict[str, Any]) -> str:
        """
        Determine query type to help hybrid search adjust weights.
        
        Returns:
            - technical: Heavy focus on specific technical skills
            - soft_skills: Focus on leadership, communication, etc.
            - experience: Focus on years of experience or seniority
            - exact_match: Looking for very specific criteria
            - exploratory: Broad, open-ended search
        """
        query_lower = parsed.get("original_query", "").lower()
        skills = parsed.get("skills", [])
        
        # Check for exact match indicators
        exact_indicators = ["exactly", "must have", "required", "mandatory", "specifically"]
        if any(indicator in query_lower for indicator in exact_indicators):
            return "exact_match"
        
        # Check for soft skills focus
        soft_skills_terms = [
            "leadership", "communication", "team", "mentor", "collaborate",
            "manage", "lead", "interpersonal", "present", "client-facing"
        ]
        soft_skills_count = sum(1 for term in soft_skills_terms if term in query_lower)
        if soft_skills_count >= 2:
            return "soft_skills"
        
        # Check for experience focus
        experience_terms = ["years", "experience", "senior", "junior", "lead", "principal", "entry"]
        if any(term in query_lower for term in experience_terms) and len(skills) < 2:
            return "experience"
        
        # Check for technical focus
        if len(skills) >= 3 or any(len(skill) > 15 for skill in skills):  # Long technical terms
            return "technical"
        
        # Default to exploratory for broad searches
        if len(skills) <= 1 and len(query_lower.split()) <= 3:
            return "exploratory"
        
        # Default to technical if skills are present
        return "technical" if skills else "exploratory"
    
    def _merge_analyses(self, basic: Dict[str, Any], gpt: Dict[str, Any]) -> Dict[str, Any]:
        """Merge basic parse with GPT-4.1-mini analysis."""
        # Deep copy GPT analysis to avoid modifying original
        import copy
        merged = copy.deepcopy(gpt)
        
        # Preserve original query info from basic parse
        merged["original_query"] = basic["original_query"]
        if basic.get("corrected_query"):
            merged["corrected_query"] = basic["corrected_query"]
        
        # Deduplicate skills across all categories (case-insensitive)
        def dedupe_skills(skills_list):
            seen = {}
            result = []
            for skill in skills_list:
                skill_lower = skill.lower()
                if skill_lower not in seen:
                    seen[skill_lower] = skill
                    result.append(skill)
            return result
        
        primary_skills = dedupe_skills(merged.get("primary_skills", []))
        secondary_skills = dedupe_skills(merged.get("secondary_skills", []))
        implied_skills = dedupe_skills(merged.get("implied_skills", []))
        
        # Ensure basic parse skills are included without duplication
        for skill in basic.get("skills", []):
            skill_lower = skill.lower()
            # Check if skill already exists (case-insensitive)
            primary_lower = [s.lower() for s in primary_skills]
            secondary_lower = [s.lower() for s in secondary_skills]
            
            if skill_lower not in primary_lower and skill_lower not in secondary_lower:
                if len(primary_skills) < 3:
                    primary_skills.append(skill)
                else:
                    secondary_skills.append(skill)
        
        # Remove any skills from implied that are in primary or secondary
        all_explicit_skills_lower = [s.lower() for s in primary_skills + secondary_skills]
        implied_skills = [s for s in implied_skills if s.lower() not in all_explicit_skills_lower]
        
        # Update merged with deduplicated skills
        merged["primary_skills"] = primary_skills
        merged["secondary_skills"] = secondary_skills
        merged["implied_skills"] = implied_skills
        
        # Add basic parse info that might be missing
        if basic.get("experience_years") and not merged.get("experience_years_min"):
            merged["experience_years_min"] = basic["experience_years"]
        
        return merged
    
    async def expand_query(self, query: str, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate expanded query variations for better search coverage.
        
        Args:
            query: Original query
            analysis: Query analysis results
            
        Returns:
            List of expanded query variations
        """
        expansions = [query]  # Always include original
        
        # Add skill-based expansions
        primary_skills = analysis.get("primary_skills", [])
        if primary_skills:
            # Single skill queries
            for skill in primary_skills[:2]:
                expansions.append(f"{skill} developer")
                expansions.append(f"{skill} engineer")
            
            # Combined skill queries
            if len(primary_skills) >= 2:
                expansions.append(f"{primary_skills[0]} {primary_skills[1]} developer")
        
        # Add role-based expansions
        role_type = analysis.get("role_type")
        experience_level = analysis.get("experience_level")
        
        if role_type and role_type != "any":
            if experience_level and experience_level != "any":
                expansions.append(f"{experience_level} {role_type} developer")
            else:
                expansions.append(f"{role_type} developer")
        
        # Add implied skill combinations
        implied_skills = analysis.get("implied_skills", [])
        for implied in implied_skills[:2]:
            if primary_skills:
                expansions.append(f"{primary_skills[0]} {implied}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_expansions = []
        for exp in expansions:
            exp_lower = exp.lower()
            if exp_lower not in seen:
                seen.add(exp_lower)
                unique_expansions.append(exp)
        
        return unique_expansions[:5]  # Limit to 5 variations
    
    def get_search_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate search suggestions based on query analysis."""
        suggestions = []
        seen_suggestions = set()
        
        # Helper to add unique suggestions
        def add_suggestion(suggestion: str):
            suggestion_lower = suggestion.lower()
            if suggestion_lower not in seen_suggestions:
                seen_suggestions.add(suggestion_lower)
                suggestions.append(suggestion)
        
        # Suggest adding missing common skills
        primary_skills = [s.lower() for s in analysis.get("primary_skills", [])]
        all_skills = primary_skills + [s.lower() for s in analysis.get("secondary_skills", [])]
        
        common_combinations = {
            "python": ["django", "flask", "fastapi"],
            "javascript": ["react", "node.js", "typescript"],
            "java": ["spring", "hibernate", "maven"],
            "devops": ["kubernetes", "terraform", "aws"]
        }
        
        # Only process each base skill once
        processed_base_skills = set()
        for skill in primary_skills:
            base_skill = skill.lower()
            if base_skill in common_combinations and base_skill not in processed_base_skills:
                processed_base_skills.add(base_skill)
                for related in common_combinations[base_skill]:
                    if related.lower() not in all_skills:
                        add_suggestion(f"Find {skill} developers with {related}")
                        break  # Only suggest one related skill per base skill
        
        # Suggest experience level if not specified
        if analysis.get("experience_level") == "any":
            add_suggestion("Add 'senior' or 'junior' to narrow results")
        
        # Suggest focusing on specific skills if too many
        if len(primary_skills) > 3:
            add_suggestion("Try searching for fewer skills for more focused results")
        elif len(primary_skills) == 0 and analysis.get("role_type") != "any":
            add_suggestion(f"Add specific skills for {analysis['role_type']} developers")
        
        return suggestions[:3]  # Limit suggestions


# Singleton instance
gpt4_analyzer = GPT4QueryAnalyzer()