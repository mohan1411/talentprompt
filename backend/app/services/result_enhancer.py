"""Result enhancement service using GPT-4.1-mini for intelligent explanations."""

import logging
import json
from typing import List, Dict, Any, Tuple, Optional
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.redis import cache_manager, RedisKeys

logger = logging.getLogger(__name__)


class ResultEnhancer:
    """
    Enhances search results with GPT-4.1-mini generated insights:
    - Detailed match explanations
    - Hidden gem detection
    - Skill transferability analysis
    - Red flag identification
    - Comparative strengths/weaknesses
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = settings.OPENAI_MODEL  # gpt-4.1-mini-2025-04-14
        
    async def enhance_results(
        self,
        results: List[Tuple[dict, float]],
        query: str,
        parsed_query: Dict[str, Any],
        limit: int = 10
    ) -> List[Tuple[dict, float]]:
        """
        Enhance search results with AI-generated insights.
        
        Args:
            results: List of (resume_data, score) tuples
            query: Original search query
            parsed_query: Parsed query analysis
            limit: Number of results to enhance
            
        Returns:
            Enhanced results with explanations
        """
        if not self.client or not results:
            return results
        
        # Enhance top results
        enhanced_results = []
        
        for i, (resume_data, score) in enumerate(results[:limit]):
            try:
                # Generate enhancement for this candidate
                enhancement = await self._enhance_single_result(
                    resume_data,
                    score,
                    query,
                    parsed_query,
                    rank=i + 1
                )
                
                # Add enhancement to resume data
                enhanced_resume = resume_data.copy()
                enhanced_resume.update(enhancement)
                
                enhanced_results.append((enhanced_resume, score))
                
            except Exception as e:
                logger.error(f"Error enhancing result {i+1}: {e}")
                # Keep original if enhancement fails
                enhanced_results.append((resume_data, score))
        
        # Add remaining results without enhancement
        enhanced_results.extend(results[limit:])
        
        return enhanced_results
    
    async def _enhance_single_result(
        self,
        resume_data: dict,
        score: float,
        query: str,
        parsed_query: Dict[str, Any],
        rank: int
    ) -> Dict[str, Any]:
        """Enhance a single search result."""
        # Check cache first
        cache_key = f"enhancement:{RedisKeys.hash_text(query)}:{resume_data['id']}"
        
        cached = await cache_manager.get_or_set(
            key=cache_key,
            fetch_func=lambda: self._generate_enhancement(
                resume_data, score, query, parsed_query, rank
            ),
            ttl=3600,  # 1 hour cache
            serialize=True
        )
        
        return cached
    
    async def _generate_enhancement(
        self,
        resume_data: dict,
        score: float,
        query: str,
        parsed_query: Dict[str, Any],
        rank: int
    ) -> Dict[str, Any]:
        """Generate AI enhancement for a candidate."""
        try:
            # Build the prompt
            system_prompt = self._build_enhancement_system_prompt()
            user_prompt = self._build_enhancement_user_prompt(
                resume_data, score, query, parsed_query, rank
            )
            
            # Call GPT-4.1-mini
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=400,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            enhancement = json.loads(response.choices[0].message.content)
            
            return enhancement
            
        except Exception as e:
            logger.error(f"Error generating enhancement: {e}")
            # Return basic enhancement
            return self._generate_basic_enhancement(resume_data, score, parsed_query)
    
    def _build_enhancement_system_prompt(self) -> str:
        """Build system prompt for enhancement generation."""
        return """You are an expert technical recruiter providing insights on candidate matches.

Analyze the candidate against the search requirements and provide a JSON response with:
{
    "match_explanation": "2-3 sentences explaining why this is a good/poor match",
    "key_strengths": ["up to 3 standout strengths relevant to the query"],
    "potential_concerns": ["any gaps or concerns, if applicable"],
    "hidden_gems": ["unexpected valuable skills or experiences"],
    "interview_focus": ["suggested areas to explore in interview"],
    "overall_fit": "excellent/strong/good/fair/poor",
    "confidence": 0.0-1.0,
    "hiring_recommendation": "One sentence actionable recommendation"
}

Be specific and reference actual skills/experience. Focus on value to the employer.
For lower-ranked candidates, be honest about gaps but also highlight any positives."""
    
    def _build_enhancement_user_prompt(
        self,
        resume_data: dict,
        score: float,
        query: str,
        parsed_query: Dict[str, Any],
        rank: int
    ) -> str:
        """Build user prompt with candidate details."""
        # Prepare candidate summary
        candidate_summary = f"""
Candidate: {resume_data.get('first_name', '')} {resume_data.get('last_name', '')}
Current Role: {resume_data.get('current_title', 'Not specified')}
Experience: {resume_data.get('years_experience', 'Unknown')} years
Skills: {', '.join(resume_data.get('skills', [])[:15])}
Location: {resume_data.get('location', 'Not specified')}

Search Query: "{query}"
Required Skills: {', '.join(parsed_query.get('primary_skills', []))}
Nice-to-have: {', '.join(parsed_query.get('secondary_skills', []))}
Match Score: {score:.2f}
Rank: #{rank}
"""
        
        # Add skill analysis if available
        if resume_data.get('skill_analysis'):
            analysis = resume_data['skill_analysis']
            candidate_summary += f"""
Matched Skills: {', '.join(analysis.get('matched', []))}
Missing Skills: {', '.join(analysis.get('missing', []))}
"""
        
        return f"Analyze this candidate match:\n{candidate_summary}"
    
    def _generate_basic_enhancement(
        self,
        resume_data: dict,
        score: float,
        parsed_query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate basic enhancement without AI."""
        # Determine overall fit based on score
        if score > 0.8:
            overall_fit = "excellent"
            explanation = "Strong match with most required skills"
        elif score > 0.6:
            overall_fit = "good"
            explanation = "Good match with key skills present"
        elif score > 0.4:
            overall_fit = "fair"
            explanation = "Partial match with some relevant skills"
        else:
            overall_fit = "poor"
            explanation = "Limited match to requirements"
        
        # Build key strengths from matched skills
        key_strengths = []
        if resume_data.get('skill_analysis'):
            for skill in resume_data['skill_analysis'].get('matched', [])[:3]:
                key_strengths.append(f"Has {skill} experience")
        
        # Note missing skills as concerns
        potential_concerns = []
        if resume_data.get('skill_analysis'):
            missing = resume_data['skill_analysis'].get('missing', [])
            if missing:
                potential_concerns.append(f"Missing: {', '.join(missing[:3])}")
        
        return {
            "match_explanation": explanation,
            "key_strengths": key_strengths,
            "potential_concerns": potential_concerns,
            "hidden_gems": [],
            "interview_focus": ["Verify technical skills", "Assess cultural fit"],
            "overall_fit": overall_fit,
            "confidence": score,
            "hiring_recommendation": f"Consider for interview" if score > 0.5 else "May not be suitable"
        }
    
    async def generate_comparative_analysis(
        self,
        candidates: List[Tuple[dict, float]],
        query: str,
        parsed_query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comparative analysis of multiple candidates.
        
        Args:
            candidates: List of top candidates to compare
            query: Original search query
            parsed_query: Parsed query analysis
            
        Returns:
            Comparative analysis
        """
        if not self.client or len(candidates) < 2:
            return {"error": "Need at least 2 candidates for comparison"}
        
        try:
            # Build comparison prompt
            system_prompt = """You are an expert recruiter providing comparative analysis of candidates.

Analyze the candidates and provide a JSON response with:
{
    "summary": "Brief overview of the candidate pool quality",
    "top_choice": {
        "name": "Candidate name",
        "reasoning": "Why they're the top choice"
    },
    "comparison_matrix": [
        {
            "name": "Candidate name",
            "strengths": ["key strengths"],
            "weaknesses": ["key gaps"],
            "unique_value": "What sets them apart",
            "risk_level": "low/medium/high",
            "recommendation": "hire/interview/pass"
        }
    ],
    "team_composition": "How these candidates would complement each other if hiring multiple",
    "market_insights": "What this candidate pool reveals about the talent market"
}"""
            
            # Build candidate summaries
            candidate_summaries = []
            for i, (resume_data, score) in enumerate(candidates[:5]):  # Compare top 5
                summary = f"""
Candidate {i+1}: {resume_data.get('first_name', '')} {resume_data.get('last_name', '')}
Role: {resume_data.get('current_title', 'N/A')}
Experience: {resume_data.get('years_experience', '?')} years
Skills: {', '.join(resume_data.get('skills', [])[:10])}
Match Score: {score:.2f}
"""
                candidate_summaries.append(summary)
            
            user_prompt = f"""Compare these candidates for the search: "{query}"
Required: {', '.join(parsed_query.get('primary_skills', []))}

{chr(10).join(candidate_summaries)}"""
            
            # Get AI analysis
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error generating comparative analysis: {e}")
            return {"error": str(e)}
    
    async def detect_hidden_gems(
        self,
        results: List[Tuple[dict, float]],
        query: str,
        parsed_query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify hidden gem candidates who might be overlooked.
        
        Args:
            results: All search results
            query: Original query
            parsed_query: Parsed query
            
        Returns:
            List of hidden gems with explanations
        """
        hidden_gems = []
        
        # Look for candidates with:
        # 1. Lower scores but transferable skills
        # 2. Different job titles but relevant experience
        # 3. Strong adjacent skills
        
        for resume_data, score in results:
            # Skip high-scoring obvious matches
            if score > 0.7:
                continue
            
            # Check for transferable skills
            gem_indicators = []
            
            # Check for related technologies
            skills = [s.lower() for s in resume_data.get('skills', [])]
            skill_families = {
                "python": ["django", "flask", "fastapi", "pandas"],
                "javascript": ["typescript", "react", "angular", "vue"],
                "aws": ["cloud", "devops", "terraform", "docker"],
                "java": ["spring", "kotlin", "scala", "jvm"]
            }
            
            for primary_skill in parsed_query.get('primary_skills', []):
                if primary_skill in skill_families:
                    related_skills = [s for s in skills if s in skill_families[primary_skill]]
                    if related_skills and primary_skill not in skills:
                        gem_indicators.append(
                            f"Has {', '.join(related_skills)} (related to {primary_skill})"
                        )
            
            # Check for leadership/mentoring if senior role
            if parsed_query.get('experience_level') in ['senior', 'lead']:
                leadership_keywords = ['lead', 'mentor', 'architect', 'principal', 'staff']
                if any(keyword in resume_data.get('current_title', '').lower() for keyword in leadership_keywords):
                    gem_indicators.append("Leadership experience")
            
            # Check years of experience
            if resume_data.get('years_experience', 0) > 7:
                gem_indicators.append(f"{resume_data['years_experience']} years experience")
            
            if gem_indicators and len(hidden_gems) < 3:
                hidden_gems.append({
                    "candidate": f"{resume_data['first_name']} {resume_data['last_name']}",
                    "current_role": resume_data.get('current_title'),
                    "why_hidden_gem": gem_indicators,
                    "recommendation": "Worth considering despite lower match score",
                    "score": score
                })
        
        return hidden_gems


# Singleton instance
result_enhancer = ResultEnhancer()