from typing import Dict, List, Optional, Any
import openai
import json
import re
from datetime import datetime
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class InterviewCopilotService:
    """AI-powered real-time interview assistant service"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
    async def analyze_transcript(
        self,
        transcript: str,
        current_question: Optional[str] = None,
        candidate_info: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze interview transcript in real-time and provide insights
        
        Args:
            transcript: The current interview transcript
            current_question: The question being discussed
            candidate_info: Information about the candidate
            context: Additional context (expected answer points, category, etc.)
        
        Returns:
            Dict containing insights, questions, fact checks, and sentiment
        """
        try:
            # Extract recent conversation (last ~1000 chars for context)
            recent_transcript = transcript[-1000:] if len(transcript) > 1000 else transcript
            
            # Build context for AI
            analysis_context = self._build_analysis_context(
                recent_transcript, current_question, candidate_info, context
            )
            
            # Call GPT-4.1-mini for analysis
            response = await self._get_ai_analysis(analysis_context)
            
            # Parse and structure the response
            structured_response = self._parse_ai_response(response)
            
            # Add real-time insights
            structured_response['insights'] = self._generate_insights(
                structured_response, recent_transcript, current_question
            )
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Copilot analysis error: {str(e)}")
            # Return fallback analysis
            return self._generate_fallback_analysis(transcript, current_question)
    
    def _build_analysis_context(
        self,
        transcript: str,
        current_question: Optional[str],
        candidate_info: Optional[Dict],
        context: Optional[Dict]
    ) -> str:
        """Build context string for AI analysis"""
        
        context_parts = []
        
        if candidate_info:
            context_parts.append(f"Candidate: {candidate_info.get('name', 'Unknown')}")
            if candidate_info.get('role'):
                context_parts.append(f"Role: {candidate_info['role']}")
        
        if current_question:
            context_parts.append(f"Current Question: {current_question}")
            
        if context:
            if context.get('expected_answer_points'):
                context_parts.append(f"Expected Points: {', '.join(context['expected_answer_points'])}")
            if context.get('category'):
                context_parts.append(f"Question Category: {context['category']}")
        
        context_parts.append(f"\nRecent Transcript:\n{transcript}")
        
        return "\n".join(context_parts)
    
    async def _get_ai_analysis(self, context: str) -> str:
        """Get AI analysis using GPT-4.1-mini"""
        
        prompt = f"""You are an expert interview copilot providing real-time assistance to interviewers. 
Analyze the following interview segment and provide actionable insights.

{context}

Provide a JSON response with the following structure:
{{
    "suggestedQuestions": [
        // 3-5 follow-up questions based on the conversation
        "question1",
        "question2",
        "question3"
    ],
    "factChecks": [
        {{
            "claim": "specific claim made by candidate",
            "verified": true/false/null,
            "explanation": "brief explanation",
            "confidence": 0.0-1.0
        }}
    ],
    "sentiment": {{
        "overall": "positive/neutral/negative/stressed",
        "confidence": 0.0-1.0,
        "indicators": ["specific behavioral indicators"],
        "trend": "improving/stable/declining"
    }},
    "keyMoments": [
        // Important moments or quotes from the conversation
        "moment1",
        "moment2"
    ],
    "recommendations": {{
        "immediate": "What to do right now",
        "followUp": "What to explore next"
    }}
}}

Focus on:
1. Detecting incomplete or vague answers that need clarification
2. Identifying technical claims that should be verified
3. Spotting signs of stress or discomfort
4. Suggesting natural follow-up questions
5. Highlighting impressive or concerning responses
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert interview copilot."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Try to parse the entire response as JSON
                return json.loads(response)
                
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response as JSON")
            return {
                "suggestedQuestions": [],
                "factChecks": [],
                "sentiment": {
                    "overall": "neutral",
                    "confidence": 0.5,
                    "indicators": [],
                    "trend": "stable"
                },
                "keyMoments": [],
                "recommendations": {
                    "immediate": "",
                    "followUp": ""
                }
            }
    
    def _generate_insights(
        self,
        ai_analysis: Dict[str, Any],
        transcript: str,
        current_question: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate actionable insights from AI analysis"""
        
        insights = []
        
        # Check for short responses
        if current_question and len(transcript.strip()) < 150:
            insights.append({
                "type": "tip",
                "title": "Short Response Detected",
                "content": "Consider asking for more detail or specific examples.",
                "priority": "medium"
            })
        
        # Add insights based on sentiment
        sentiment = ai_analysis.get('sentiment', {})
        if sentiment.get('overall') == 'stressed':
            insights.append({
                "type": "warning",
                "title": "Stress Indicators Detected",
                "content": "The candidate may be feeling nervous. Consider a lighter question.",
                "priority": "high"
            })
        elif sentiment.get('overall') == 'positive':
            insights.append({
                "type": "highlight",
                "title": "Positive Engagement",
                "content": "Good time to explore deeper technical topics.",
                "priority": "low"
            })
        
        # Add fact-check insights
        fact_checks = ai_analysis.get('factChecks', [])
        for fact in fact_checks:
            if fact.get('verified') is False:
                insights.append({
                    "type": "fact_check",
                    "title": "Claim Needs Verification",
                    "content": f"{fact['claim']} - {fact['explanation']}",
                    "priority": "high"
                })
        
        # Add recommendation as insight if present
        recommendations = ai_analysis.get('recommendations', {})
        if recommendations.get('immediate'):
            insights.append({
                "type": "question",
                "title": "Recommended Action",
                "content": recommendations['immediate'],
                "priority": "medium"
            })
        
        return insights
    
    def _generate_fallback_analysis(
        self,
        transcript: str,
        current_question: Optional[str]
    ) -> Dict[str, Any]:
        """Generate basic analysis when AI is unavailable"""
        
        # Simple local analysis
        words = transcript.lower().split()
        
        # Basic sentiment detection
        positive_words = ['excellent', 'great', 'love', 'passionate', 'excited']
        negative_words = ['difficult', 'challenge', 'struggle', 'hard']
        stress_indicators = ['um', 'uh', 'well', 'actually', 'like']
        
        positive_count = sum(1 for w in words if w in positive_words)
        negative_count = sum(1 for w in words if w in negative_words)
        stress_count = sum(1 for w in words if w in stress_indicators)
        
        overall_sentiment = 'neutral'
        if stress_count > 10:
            overall_sentiment = 'stressed'
        elif positive_count > negative_count + 2:
            overall_sentiment = 'positive'
        elif negative_count > positive_count + 2:
            overall_sentiment = 'negative'
        
        # Generate basic suggestions based on question category
        suggested_questions = []
        if current_question:
            if 'technical' in current_question.lower():
                suggested_questions = [
                    "Can you provide more technical details?",
                    "What specific technologies did you use?",
                    "How did you handle challenges?"
                ]
            else:
                suggested_questions = [
                    "Can you give me a specific example?",
                    "What was the outcome?",
                    "How did you measure success?"
                ]
        
        return {
            "suggestedQuestions": suggested_questions,
            "factChecks": [],
            "sentiment": {
                "overall": overall_sentiment,
                "confidence": 0.6,
                "indicators": ["High filler word count"] if stress_count > 10 else [],
                "trend": "stable"
            },
            "keyMoments": [],
            "insights": [
                {
                    "type": "tip",
                    "title": "AI Analysis Unavailable",
                    "content": "Using basic pattern matching for insights.",
                    "priority": "low"
                }
            ]
        }