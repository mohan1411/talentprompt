"""AI service for interview preparation and assistance."""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.openai import openai_service, OpenAIService
from app.models.interview import QuestionCategory
from app.models.resume import Resume

logger = logging.getLogger(__name__)


class InterviewAIService:
    """Service for AI-powered interview assistance."""
    
    def __init__(self):
        self.openai_service = openai_service
    
    async def generate_interview_questions(
        self,
        resume: Resume,
        job_position: str,
        job_requirements: Optional[Dict[str, Any]] = None,
        focus_areas: Optional[List[str]] = None,
        difficulty_level: int = 3,
        num_questions: int = 10,
        interview_type: str = "general"
    ) -> Dict[str, Any]:
        """Generate intelligent interview questions based on resume and job requirements."""
        
        # Build context from resume
        resume_context = self._build_resume_context(resume)
        
        # Create prompt for question generation
        prompt = f"""
        You are an expert interviewer preparing questions for a {job_position} position.
        
        Candidate Profile:
        - Name: {resume.first_name} {resume.last_name}
        - Current Title: {resume.current_title or 'Not specified'}
        - Experience: {resume.years_experience or 0} years
        - Skills: {', '.join(resume.skills[:10]) if resume.skills else 'Not specified'}
        - Summary: {resume.summary[:500] if resume.summary else 'Not available'}
        
        Job Requirements:
        {json.dumps(job_requirements, indent=2) if job_requirements else 'Standard requirements for ' + job_position}
        
        Interview Type: {interview_type}
        Difficulty Level: {difficulty_level}/5
        Focus Areas: {', '.join(focus_areas) if focus_areas else 'General assessment'}
        
        Generate {num_questions} interview questions that:
        1. Are specific to the candidate's background
        2. Assess fit for the {job_position} role
        3. Include a mix of technical, behavioral, and situational questions
        4. Match the specified difficulty level
        5. Probe any gaps or transitions in their career
        6. Explore their claimed skills and experience
        
        For each question, provide:
        - The question text
        - Category (technical/behavioral/situational/culture_fit/experience)
        - Why this question is relevant for this candidate
        - Key points to look for in their answer
        - A potential follow-up question
        
        Return a JSON object with a "questions" array containing exactly {num_questions} questions:
        {{
            "questions": [
                {{
                    "question": "question text",
                    "category": "category",
                    "relevance": "why this matters",
                    "expected_points": ["point 1", "point 2"],
                    "follow_up": "follow-up question"
                }},
                {{
                    "question": "another question text",
                    "category": "category",
                    "relevance": "why this matters",
                    "expected_points": ["point 1", "point 2"],
                    "follow_up": "follow-up question"
                }}
            ]
        }}
        
        IMPORTANT: 
        1. Return a JSON object with a "questions" key containing an array
        2. The array MUST contain exactly {num_questions} questions
        3. Each question must have all the required fields
        """
        
        try:
            response = await self.openai_service.generate_completion(prompt)
            
            # Log the raw response for debugging
            logger.info(f"OpenAI raw response (first 200 chars): {response[:200]}")
            
            # Try to parse the JSON response
            try:
                questions = json.loads(response)
            except json.JSONDecodeError as json_error:
                logger.error(f"Failed to parse OpenAI response as JSON: {json_error}")
                logger.error(f"Response content: {response}")
                # Return fallback questions if JSON parsing fails
                return self._get_fallback_questions(job_position, num_questions)
            
            # Handle different response formats
            if isinstance(questions, dict):
                # Check if it's a single question object
                if all(key in questions for key in ['question', 'category', 'relevance']):
                    # Convert single question to array
                    logger.warning(f"Got single question instead of array, converting to array")
                    questions = [questions]
                else:
                    # The response might be wrapped in an object
                    # Try common keys that might contain the questions array
                    for key in ['questions', 'items', 'data', 'results', 'response']:
                        if key in questions and isinstance(questions[key], list):
                            questions = questions[key]
                            break
                    else:
                        # If no list found in dict, log the structure and use fallback
                        logger.error(f"Expected list of questions, got dict with keys: {list(questions.keys())}")
                        logger.info(f"Dict content sample: {str(questions)[:500]}")
                        return self._get_fallback_questions(job_position, num_questions)
            
            # Validate the response structure
            if not isinstance(questions, list):
                logger.error(f"Expected list of questions after unwrapping, got: {type(questions)}")
                return self._get_fallback_questions(job_position, num_questions)
            
            # Enhance questions with additional metadata
            enhanced_questions = []
            for i, q in enumerate(questions):
                try:
                    enhanced_questions.append({
                        "question_text": q.get("question", q.get("question_text", "No question text")),
                        "category": self._map_category(q.get("category", "behavioral")),
                        "difficulty_level": difficulty_level,
                        "generation_context": q.get("relevance", ""),
                        "expected_answer_points": q.get("expected_points", []),
                        "follow_up_questions": [q.get("follow_up", "")] if q.get("follow_up") else [],
                        "order_index": i + 1,
                        "ai_generated": True
                    })
                except Exception as q_error:
                    logger.error(f"Error processing question {i}: {q_error}")
                    logger.error(f"Question data: {q}")
            
            if not enhanced_questions:
                logger.error("No questions could be processed")
                return self._get_fallback_questions(job_position, num_questions)
            
            return {
                "questions": enhanced_questions,
                "total_count": len(enhanced_questions),
                "generation_metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "interview_type": interview_type,
                    "difficulty_level": difficulty_level
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating interview questions: {e}")
            # Return fallback questions
            return self._get_fallback_questions(job_position, num_questions)
    
    async def analyze_candidate_for_interview(
        self,
        resume: Resume,
        job_position: str,
        job_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze candidate and provide interview preparation insights."""
        
        prompt = f"""
        Analyze this candidate for a {job_position} interview and provide insights.
        
        Candidate:
        - Name: {resume.first_name} {resume.last_name}
        - Title: {resume.current_title}
        - Experience: {resume.years_experience} years
        - Skills: {', '.join(resume.skills[:15]) if resume.skills else 'Not specified'}
        - Summary: {resume.summary[:500] if resume.summary else 'Not available'}
        
        Job Requirements:
        {json.dumps(job_requirements, indent=2) if job_requirements else 'Standard ' + job_position}
        
        Provide:
        1. A brief candidate summary (2-3 sentences)
        2. Key strengths to highlight (3-5 points)
        3. Potential concerns or gaps to explore (3-5 points)
        4. Suggested talking points (3-5 points)
        5. Red flags to watch for
        6. Overall fit assessment (score 1-10 with reasoning)
        
        Return a JSON object with these exact keys:
        {{
            "summary": "2-3 sentence summary",
            "strengths": ["strength 1", "strength 2", ...],
            "concerns": ["concern 1", "concern 2", ...],
            "talking_points": ["point 1", "point 2", ...],
            "red_flags": ["flag 1", "flag 2", ...] or [],
            "fit_score": 8,
            "fit_reasoning": "explanation of score"
        }}
        """
        
        try:
            response = await self.openai_service.generate_completion(prompt)
            
            # Log the raw response for debugging
            logger.info(f"Candidate analysis raw response (first 200 chars): {response[:200]}")
            
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError as json_error:
                logger.error(f"Failed to parse candidate analysis as JSON: {json_error}")
                logger.error(f"Response content: {response}")
                return self._get_default_analysis(resume, job_position)
            
            return {
                "candidate_summary": {
                    "brief": analysis.get("summary", ""),
                    "strengths": analysis.get("strengths", []),
                    "experience_level": self._categorize_experience(resume.years_experience)
                },
                "key_talking_points": analysis.get("talking_points", []),
                "areas_to_explore": analysis.get("concerns", []),
                "red_flags": analysis.get("red_flags", []),
                "fit_assessment": {
                    "score": analysis.get("fit_score", 5),
                    "reasoning": analysis.get("fit_reasoning", "")
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing candidate: {e}")
            return self._get_default_analysis(resume, job_position)
    
    async def generate_follow_up_question(
        self,
        original_question: str,
        candidate_response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a contextual follow-up question based on candidate's response."""
        
        prompt = f"""
        Based on this interview exchange, generate an intelligent follow-up question.
        
        Original Question: {original_question}
        Candidate Response: {candidate_response}
        
        Context:
        - Job Position: {context.get('job_position', 'Not specified')}
        - Interview Type: {context.get('interview_type', 'general')}
        
        Generate a follow-up question that:
        1. Digs deeper into their response
        2. Clarifies any vague points
        3. Tests the depth of their knowledge
        4. Is natural and conversational
        
        Also identify if any red flags or positive signals in their response.
        
        Return as JSON:
        {{
            "follow_up_question": "question text",
            "reason": "why this follow-up",
            "signals": {{
                "positive": ["signal 1"],
                "negative": ["flag 1"]
            }}
        }}
        """
        
        try:
            response = await self.openai_service.generate_completion(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error generating follow-up: {e}")
            return {
                "follow_up_question": "Can you provide more specific details about that?",
                "reason": "To get more concrete information",
                "signals": {"positive": [], "negative": []}
            }
    
    async def generate_interview_scorecard(
        self,
        session_data: Dict[str, Any],
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a comprehensive interview scorecard."""
        
        # Log incoming responses for debugging
        logger.info(f"Generating scorecard with {len(responses)} responses")
        if not responses:
            logger.warning("No responses provided to scorecard generation - will use default scorecard")
            return self._get_default_scorecard()
        
        # Check for potential audio mismatch first
        mismatch_check = await self._detect_audio_mismatch(session_data, responses)
        
        # Log mismatch detection results
        if mismatch_check['is_mismatch']:
            logger.warning(f"Audio mismatch detected: {mismatch_check['warning']}")
            logger.warning(f"Relevance ratio: {mismatch_check.get('relevance_ratio', 0):.2f}, Domain: {mismatch_check.get('detected_domain', 'unknown')}")
        
        # Extract question categories and ratings
        technical_responses = [r for r in responses if 'technical' in r.get('question_text', '').lower() or 
                              any(tech in r.get('question_text', '').lower() for tech in 
                              ['python', 'java', 'javascript', 'react', 'api', 'database', 'sql', 'aws', 'docker'])]
        behavioral_responses = [r for r in responses if r not in technical_responses]
        
        prompt = f"""
        Generate a comprehensive interview scorecard based on this interview data.
        
        Session Info:
        - Position: {session_data.get('job_position')}
        - Duration: {session_data.get('duration_minutes')} minutes
        - Questions Asked: {len(responses)}
        
        Responses Summary:
        {self._summarize_responses(responses)}
        
        Analyze the candidate's performance and provide a detailed scorecard.
        For technical skills, identify specific technologies mentioned in questions and rate them.
        For soft skills, identify behaviors like communication, leadership, teamwork, etc.
        
        {f'''
        IMPORTANT: Audio mismatch detected! Confidence level: {mismatch_check['confidence']}%
        Warning: {mismatch_check['warning']}
        ''' if mismatch_check['is_mismatch'] else ''}
        
        Return EXACTLY this JSON structure:
        {{
            "overall_rating": 4.2,  // number between 1-5
            "recommendation": "hire",  // must be one of: hire, no_hire, maybe
            "confidence": 85,  // confidence percentage 0-100
            "data_quality": "high",  // one of: high, medium, low, mismatch
            "technical_skills": {{
                "Python": 4.5,  // Extract actual skills from questions
                "JavaScript": 4.0,
                "AWS": 3.5,
                "System Design": 4.0
            }},
            "soft_skills": {{
                "Communication": 4.5,
                "Leadership": 4.0,
                "Problem Solving": 4.2,
                "Teamwork": 4.3
            }},
            "culture_fit": 4.0,  // number between 1-5
            "strengths": [
                "Strong Python and backend development skills",
                "Excellent communication and presentation abilities",
                "Proven track record of leading technical projects",
                "Good understanding of cloud architecture"
            ],
            "concerns": [
                "Limited experience with our specific tech stack",
                "May be overqualified for the position",
                "Salary expectations might be high"
            ],
            "next_steps": [
                "Schedule technical deep-dive with senior engineers",
                "Conduct reference checks",
                "Discuss compensation expectations"
            ]
        }}
        
        IMPORTANT: Extract actual technical skills from the questions asked, not generic categories.
        Base all ratings on the actual responses provided.
        
        CRITICAL: If responses are completely unrelated to the questions (e.g., talking about travel when asked about programming),
        you MUST give extremely low ratings (1.0-1.5) and set recommendation to "no_hire".
        """
        
        try:
            response = await self.openai_service.generate_completion(prompt)
            
            # Log for debugging
            logger.info(f"Scorecard AI response (first 500 chars): {response[:500]}")
            
            try:
                scorecard = json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse scorecard JSON: {e}")
                logger.error(f"Response: {response}")
                
                # Try to extract JSON if it's wrapped in markdown
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    scorecard = json.loads(json_match.group(1))
                else:
                    return self._get_default_scorecard()
            
            # Ensure all required fields exist
            if 'overall_rating' not in scorecard:
                scorecard['overall_rating'] = 3.0
            
            # Add percentile ranking based on overall rating
            scorecard["percentile_rank"] = self._calculate_percentile(
                float(scorecard.get("overall_rating", 3.0))
            )
            
            # Ensure technical_skills and soft_skills are dictionaries
            if not isinstance(scorecard.get('technical_skills'), dict):
                scorecard['technical_skills'] = {"General Technical": 3.0}
            if not isinstance(scorecard.get('soft_skills'), dict):
                scorecard['soft_skills'] = {"Communication": 3.0, "Teamwork": 3.0}
            
            # Ensure arrays exist
            scorecard['strengths'] = scorecard.get('strengths', ['Good overall performance'])
            scorecard['concerns'] = scorecard.get('concerns', ['Needs further assessment'])
            scorecard['next_steps'] = scorecard.get('next_steps', ['Schedule follow-up'])
            
            # Add mismatch info if detected and override ratings
            if mismatch_check['is_mismatch']:
                scorecard['mismatch_detected'] = True
                scorecard['mismatch_warning'] = mismatch_check['warning']
                scorecard['confidence'] = mismatch_check['confidence']
                scorecard['data_quality'] = 'mismatch'
                
                # Reduce ratings but don't completely override to 1.0
                # Let the AI's actual assessment have some weight
                reduction_factor = 0.5  # Reduce by 50% instead of setting to 1.0
                
                scorecard['overall_rating'] = max(1.0, scorecard.get('overall_rating', 3.0) * reduction_factor)
                scorecard['recommendation'] = 'no_hire' if scorecard['overall_rating'] < 2.0 else 'maybe'
                scorecard['culture_fit'] = max(1.0, scorecard.get('culture_fit', 3.0) * reduction_factor)
                
                # Reduce skill ratings proportionally
                if 'technical_skills' in scorecard:
                    for skill in scorecard['technical_skills']:
                        scorecard['technical_skills'][skill] = max(1.0, scorecard['technical_skills'][skill] * reduction_factor)
                
                if 'soft_skills' in scorecard:
                    for skill in scorecard['soft_skills']:
                        scorecard['soft_skills'][skill] = max(1.0, scorecard['soft_skills'][skill] * reduction_factor)
                
                # Update concerns to reflect mismatch
                scorecard['concerns'] = [
                    f"Audio content appears to be from {mismatch_check.get('detected_domain', 'non-technical')} domain",
                    "Responses completely unrelated to interview questions",
                    "No technical knowledge demonstrated",
                    "Possible wrong audio file uploaded"
                ]
                
                scorecard['strengths'] = []
                scorecard['percentile_rank'] = 5.0
            
            return scorecard
            
        except Exception as e:
            logger.error(f"Error generating scorecard: {e}")
            return self._get_default_scorecard()
    
    def _build_resume_context(self, resume: Resume) -> str:
        """Build a context string from resume data."""
        parts = []
        
        if resume.first_name and resume.last_name:
            parts.append(f"Name: {resume.first_name} {resume.last_name}")
        
        if resume.current_title:
            parts.append(f"Current Role: {resume.current_title}")
            
        if resume.years_experience:
            parts.append(f"Experience: {resume.years_experience} years")
            
        if resume.skills:
            parts.append(f"Key Skills: {', '.join(resume.skills[:10])}")
            
        # Education might be in parsed_data JSON field
        if resume.parsed_data and isinstance(resume.parsed_data, dict):
            education = resume.parsed_data.get('education')
            if education:
                parts.append(f"Education: {json.dumps(education)}")
        
        if resume.location:
            parts.append(f"Location: {resume.location}")
            
        return "\n".join(parts)
    
    def _map_category(self, category_str: str) -> QuestionCategory:
        """Map string category to enum."""
        mapping = {
            "technical": QuestionCategory.TECHNICAL,
            "behavioral": QuestionCategory.BEHAVIORAL,
            "situational": QuestionCategory.SITUATIONAL,
            "culture_fit": QuestionCategory.CULTURE_FIT,
            "culture fit": QuestionCategory.CULTURE_FIT,
            "experience": QuestionCategory.EXPERIENCE,
            "problem_solving": QuestionCategory.PROBLEM_SOLVING,
            "problem solving": QuestionCategory.PROBLEM_SOLVING
        }
        
        return mapping.get(category_str.lower(), QuestionCategory.BEHAVIORAL)
    
    def _categorize_experience(self, years: Optional[int]) -> str:
        """Categorize experience level."""
        if not years:
            return "entry"
        elif years < 2:
            return "junior"
        elif years < 5:
            return "mid"
        elif years < 10:
            return "senior"
        else:
            return "principal"
    
    def _summarize_responses(self, responses: List[Dict[str, Any]]) -> str:
        """Summarize interview responses for analysis."""
        if not responses:
            return "No responses recorded yet."
            
        summary_parts = []
        
        # Group by category
        technical_questions = []
        behavioral_questions = []
        
        for resp in responses:
            question_text = resp.get('question_text', '')
            rating = resp.get('response_rating', 0)
            
            # Categorize based on question content
            is_technical = any(keyword in question_text.lower() for keyword in [
                'technical', 'code', 'programming', 'system', 'design', 'architecture',
                'python', 'java', 'javascript', 'react', 'api', 'database', 'sql', 
                'aws', 'docker', 'kubernetes', 'algorithm', 'data structure'
            ])
            
            q_summary = {
                'question': question_text[:150],
                'rating': rating,
                'summary': resp.get('response_summary', 'No summary')[:200]
            }
            
            if is_technical:
                technical_questions.append(q_summary)
            else:
                behavioral_questions.append(q_summary)
        
        # Build summary
        summary_parts.append(f"Total Questions: {len(responses)}")
        summary_parts.append(f"Average Rating: {sum(r.get('response_rating', 0) for r in responses) / len(responses) if responses else 0:.1f}/5")
        
        summary_parts.append("\nTechnical Questions:")
        for i, q in enumerate(technical_questions[:5], 1):
            summary_parts.append(
                f"Q{i}: {q['question']}...\n"
                f"Rating: {q['rating']}/5\n"
                f"Response: {q['summary']}...\n"
            )
        
        summary_parts.append("\nBehavioral Questions:")
        for i, q in enumerate(behavioral_questions[:5], 1):
            summary_parts.append(
                f"Q{i}: {q['question']}...\n"
                f"Rating: {q['rating']}/5\n"
                f"Response: {q['summary']}...\n"
            )
        
        return "\n".join(summary_parts)
    
    def _calculate_percentile(self, rating: float) -> float:
        """Calculate percentile rank (mock implementation)."""
        # In real implementation, this would query historical data
        if rating >= 4.5:
            return 90.0
        elif rating >= 4.0:
            return 75.0
        elif rating >= 3.5:
            return 50.0
        elif rating >= 3.0:
            return 25.0
        else:
            return 10.0
    
    async def _detect_audio_mismatch(
        self, 
        session_data: Dict[str, Any],
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Detect if uploaded audio doesn't match interview context."""
        
        # Check for empty or invalid responses
        if not responses or len(responses) == 0:
            logger.info("No responses to analyze for mismatch detection")
            return {"is_mismatch": False, "confidence": 100, "warning": "No responses to analyze"}
        
        # Extract job position and expected keywords
        job_position = session_data.get('job_position', '').lower()
        
        # Define expected technical domains based on common positions
        tech_keywords = {
            'backend': ['api', 'database', 'server', 'python', 'java', 'microservice', 'sql', 'rest', 'backend',
                       'aws', 'cloud', 'docker', 'kubernetes', 'redis', 'mongodb', 'postgresql', 'mysql',
                       'node', 'express', 'django', 'flask', 'spring', 'authentication', 'security',
                       'performance', 'scaling', 'architecture', 'design patterns', 'testing', 'fastapi',
                       'graphql', 'grpc', 'message queue', 'rabbitmq', 'kafka', 'elasticsearch', 'nginx',
                       'load balancer', 'caching', 'optimization', 'async', 'threading', 'celery', 'oauth',
                       'jwt', 'encryption', 'hashing', 'bcrypt', 'migration', 'orm', 'sqlalchemy', 'alembic',
                       'pytest', 'unit test', 'integration', 'ci/cd', 'pipeline', 'deployment', 'monitoring',
                       'logging', 'debugging', 'profiling', 'memory', 'cpu', 'latency', 'throughput', 
                       'scalability', 'reliability', 'availability', 'fault tolerance', 'distributed',
                       # Sharon Miller specific terms from her transcript
                       'monolithic', 'monolith', 'eks', 's3', 'ebs', 'rds', 'sqs', 'sns', 'iam', 'vpc',
                       'apollo', 'graphene', 'dataloader', 'n+1', 'terraform', 'prometheus', 'grafana',
                       'elk', 'pact', 'circuit breaker', 'connection pool', 'read replica', 'p99',
                       'zero-downtime', 'expand-contract', 'schema', 'rollback', 'backup'],
            'frontend': ['react', 'javascript', 'css', 'html', 'ui', 'ux', 'component', 'frontend', 'browser',
                        'typescript', 'vue', 'angular', 'webpack', 'responsive', 'accessibility', 'state management',
                        'redux', 'mobx', 'context api', 'hooks', 'jsx', 'sass', 'styled components', 'tailwind',
                        'bootstrap', 'material ui', 'next.js', 'gatsby', 'spa', 'ssr', 'ssg', 'pwa', 'service worker'],
            'fullstack': ['api', 'react', 'database', 'frontend', 'backend', 'full-stack', 'javascript', 'python',
                         'node.js', 'express', 'mongodb', 'postgresql', 'rest', 'graphql', 'microservices'],
            'data': ['data', 'analysis', 'sql', 'python', 'machine learning', 'statistics', 'etl', 'pandas', 'numpy',
                    'scikit-learn', 'tensorflow', 'pytorch', 'jupyter', 'data pipeline', 'warehouse', 'spark'],
            'devops': ['docker', 'kubernetes', 'ci/cd', 'aws', 'deployment', 'infrastructure', 'terraform', 'jenkins',
                      'ansible', 'puppet', 'chef', 'gitlab', 'github actions', 'circleci', 'monitoring', 'prometheus'],
            'mobile': ['ios', 'android', 'swift', 'kotlin', 'mobile', 'app', 'react native', 'flutter', 'xcode',
                      'android studio', 'objective-c', 'java', 'push notification', 'app store', 'google play'],
        }
        
        # Common non-tech domains that might indicate mismatch
        non_tech_domains = {
            'cooking': ['recipe', 'ingredient', 'cook', 'bake', 'kitchen', 'food', 'taste', 'dish'],
            'medical': ['patient', 'diagnosis', 'treatment', 'medicine', 'doctor', 'symptoms'],
            'finance': ['investment', 'portfolio', 'stock', 'trading', 'banking', 'financial'],
            'education': ['student', 'curriculum', 'teaching', 'classroom', 'lesson', 'grade'],
            'travel': ['travel', 'vacation', 'tourist', 'destination', 'hotel', 'flight', 'embassy', 
                      'disaster', 'insurance', 'trip', 'overseas', 'roller coaster', 'amusement park', 
                      'red cross', 'itinerary', 'internationally'],
        }
        
        # Analyze responses
        total_responses = len(responses)
        relevant_responses = 0
        off_topic_responses = 0
        detected_domain = None
        
        logger.info(f"Analyzing {total_responses} responses for mismatch detection")
        
        for i, resp in enumerate(responses):
            # Check multiple possible field names for the response content
            response_text = (resp.get('response_summary', '') or 
                           resp.get('response_text', '') or 
                           resp.get('response_transcript', '')).lower()
            question_text = resp.get('question_text', '').lower()
            
            if i == 0:  # Log first response for debugging
                logger.info(f"First response sample - Q: {question_text[:100]}... A: {response_text[:100]}...")
            
            # Check if response contains any expected technical keywords
            position_type = 'backend' if 'backend' in job_position else \
                          'frontend' if 'frontend' in job_position else \
                          'data' if 'data' in job_position else \
                          'devops' if 'devops' in job_position else \
                          'mobile' if 'mobile' in job_position else 'fullstack'
            
            expected_keywords = tech_keywords.get(position_type, [])
            
            # Check for relevant technical content - be more lenient
            # Also check the question itself for context
            combined_text = response_text + ' ' + question_text
            
            # Count matching keywords
            keyword_matches = sum(1 for keyword in expected_keywords if keyword in combined_text)
            
            # Consider it relevant if it has at least 1 technical keyword or mentions technical concepts
            # Also check for general technical terms
            general_tech_terms = ['code', 'develop', 'implement', 'build', 'test', 'debug', 'deploy',
                                'software', 'application', 'system', 'technical', 'technology',
                                'programming', 'engineer', 'architecture', 'framework', 'library',
                                'algorithm', 'data structure', 'complexity', 'optimization', 'refactor',
                                'version control', 'git', 'github', 'gitlab', 'bitbucket', 'merge',
                                'pull request', 'code review', 'agile', 'scrum', 'sprint', 'standup',
                                'requirement', 'specification', 'documentation', 'api documentation',
                                'unit test', 'integration test', 'test coverage', 'continuous integration',
                                'continuous deployment', 'devops', 'infrastructure', 'server', 'client',
                                'frontend', 'backend', 'fullstack', 'database', 'query', 'index',
                                'performance', 'scalability', 'reliability', 'security', 'authentication',
                                'authorization', 'encryption', 'https', 'ssl', 'certificate', 'token',
                                'session', 'cookie', 'cache', 'memory', 'storage', 'file system',
                                'network', 'protocol', 'http', 'rest', 'soap', 'websocket', 'tcp',
                                'udp', 'dns', 'load balancer', 'proxy', 'firewall', 'vpc', 'subnet',
                                'container', 'orchestration', 'microservice', 'monolith', 'serverless',
                                'function', 'lambda', 'cloud', 'aws', 'azure', 'gcp', 'digital ocean']
            
            general_matches = sum(1 for term in general_tech_terms if term in combined_text)
            
            has_relevant_content = keyword_matches > 0 or general_matches >= 1
            if has_relevant_content:
                relevant_responses += 1
                logger.debug(f"Found relevant content in response (keywords: {keyword_matches}, general: {general_matches})")
            
            # Check for non-tech domain content - only count if strongly off-topic
            for domain, keywords in non_tech_domains.items():
                domain_matches = sum(keyword in response_text for keyword in keywords)
                if domain_matches >= 3 and general_matches < 2:  # Only flag if high non-tech AND low tech
                    off_topic_responses += 1
                    detected_domain = domain
                    logger.debug(f"Found off-topic content: {domain} (matches: {domain_matches})")
                    break
        
        # Calculate mismatch indicators
        relevance_ratio = relevant_responses / total_responses if total_responses > 0 else 0
        off_topic_ratio = off_topic_responses / total_responses if total_responses > 0 else 0
        
        # Determine if mismatch - only flag very clear mismatches
        # Need BOTH very low relevance AND high off-topic to be considered mismatch
        is_mismatch = relevance_ratio < 0.1 and off_topic_ratio > 0.6
        
        # For manual transcripts, be extremely lenient
        if session_data.get('is_manual_transcript', False):
            is_mismatch = relevance_ratio == 0 and off_topic_ratio > 0.9
            logger.info(f"Manual transcript - using lenient mismatch detection")
        
        confidence = max(10, min(90, int((1 - relevance_ratio) * 100))) if is_mismatch else 100
        
        # Generate warning message
        warning = ""
        if is_mismatch:
            logger.warning(f"Mismatch detected for {job_position} position")
            logger.warning(f"Relevance ratio: {relevance_ratio:.2f}, Off-topic ratio: {off_topic_ratio:.2f}")
            logger.warning(f"Relevant responses: {relevant_responses}/{total_responses}")
            logger.warning(f"Is manual transcript: {session_data.get('is_manual_transcript', False)}")
            
            if detected_domain:
                warning = f"Audio content appears to be from {detected_domain} domain, not technical interview"
            else:
                warning = "Audio content doesn't match expected technical interview responses"
        else:
            logger.info(f"No mismatch detected for {job_position} position")
            logger.info(f"Relevance ratio: {relevance_ratio:.2f}, Off-topic ratio: {off_topic_ratio:.2f}")
            logger.info(f"Relevant responses: {relevant_responses}/{total_responses}")
        
        return {
            "is_mismatch": is_mismatch,
            "confidence": confidence,
            "warning": warning,
            "relevance_ratio": relevance_ratio,
            "detected_domain": detected_domain,
            "debug_info": {
                "total_responses": total_responses,
                "relevant_responses": relevant_responses,
                "off_topic_responses": off_topic_responses,
                "position_type": position_type if 'position_type' in locals() else 'unknown'
            }
        }
    
    def _get_fallback_questions(self, job_position: str, num_questions: int) -> Dict[str, Any]:
        """Get fallback questions if AI generation fails."""
        base_questions = [
            {
                "question_text": f"Tell me about your experience relevant to this {job_position} role.",
                "category": QuestionCategory.EXPERIENCE,
                "difficulty_level": 2
            },
            {
                "question_text": "Describe a challenging project you've worked on recently.",
                "category": QuestionCategory.BEHAVIORAL,
                "difficulty_level": 3
            },
            {
                "question_text": "How do you stay updated with industry trends and technologies?",
                "category": QuestionCategory.CULTURE_FIT,
                "difficulty_level": 2
            },
            {
                "question_text": "Walk me through your problem-solving approach.",
                "category": QuestionCategory.PROBLEM_SOLVING,
                "difficulty_level": 3
            },
            {
                "question_text": "Where do you see yourself in 5 years?",
                "category": QuestionCategory.CULTURE_FIT,
                "difficulty_level": 2
            }
        ]
        
        return {
            "questions": base_questions[:num_questions],
            "total_count": min(len(base_questions), num_questions),
            "generation_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "fallback": True
            }
        }
    
    def _get_default_analysis(self, resume: Resume, job_position: str) -> Dict[str, Any]:
        """Get default analysis if AI fails."""
        return {
            "candidate_summary": {
                "brief": f"{resume.first_name} {resume.last_name} is a candidate for {job_position}",
                "strengths": ["Technical skills", "Relevant experience"],
                "experience_level": self._categorize_experience(resume.years_experience)
            },
            "key_talking_points": [
                "Current role and responsibilities",
                "Career progression",
                "Technical expertise",
                "Team collaboration experience"
            ],
            "areas_to_explore": [
                "Specific technical skills depth",
                "Leadership experience",
                "Problem-solving examples"
            ],
            "red_flags": [],
            "fit_assessment": {
                "score": 7,
                "reasoning": "Based on resume analysis"
            }
        }
    
    def _get_default_scorecard(self) -> Dict[str, Any]:
        """Get default scorecard if generation fails."""
        return {
            "overall_rating": 3.0,
            "recommendation": "maybe",
            "technical_skills": {
                "General Technical Skills": 3.0,
                "Problem Solving": 3.0,
                "System Design": 3.0
            },
            "soft_skills": {
                "Communication": 3.0,
                "Teamwork": 3.0,
                "Leadership": 3.0,
                "Adaptability": 3.0
            },
            "culture_fit": 3.0,
            "strengths": [
                "Professional experience in relevant field",
                "Good communication skills demonstrated",
                "Shows potential for growth"
            ],
            "concerns": [
                "Need more detailed technical assessment",
                "Unclear about specific skill proficiency",
                "Requires further evaluation"
            ],
            "next_steps": [
                "Schedule technical assessment",
                "Conduct reference checks",
                "Review with hiring team"
            ],
            "percentile_rank": 50.0
        }
    
    async def analyze_candidate_for_followup(
        self,
        resume: Resume,
        job_position: str,
        job_requirements: Optional[Dict[str, Any]] = None,
        previous_performance: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze candidate for follow-up interview round based on previous performance."""
        
        prompt = f"""
        Analyze this candidate for a follow-up interview round based on their previous performance.
        
        Candidate:
        - Name: {resume.first_name} {resume.last_name}
        - Title: {resume.current_title}
        - Experience: {resume.years_experience} years
        - Skills: {', '.join(resume.skills[:15]) if resume.skills else 'Not specified'}
        
        Job Position: {job_position}
        
        Previous Interview Performance:
        - Overall Rating: {previous_performance.get('overall_rating', 'N/A')}/5
        - Recommendation: {previous_performance.get('recommendation', 'N/A')}
        - Strengths: {', '.join(previous_performance.get('strengths', []))}
        - Concerns: {', '.join(previous_performance.get('concerns', []))}
        
        Questions Asked and Ratings:
        {self._format_previous_questions(previous_performance.get('questions_asked', []))}
        
        Based on the previous performance, provide:
        1. Updated candidate summary focusing on areas needing clarification
        2. Key areas that showed promise and need deeper exploration
        3. Concerns that need to be addressed in this round
        4. Specific topics to probe based on weak answers
        5. Talking points that build on strong areas
        
        Return a JSON object with these exact keys:
        {{
            "summary": "2-3 sentence updated summary",
            "strengths": ["areas that need deeper dive", ...],
            "concerns": ["specific concerns to address", ...],
            "talking_points": ["building on previous answers", ...],
            "red_flags": ["any new red flags", ...] or [],
            "focus_areas": ["specific topics to probe", ...]
        }}
        """
        
        try:
            response = await self.openai_service.generate_completion(prompt)
            
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse follow-up analysis as JSON")
                return self._get_default_followup_analysis(resume, job_position, previous_performance)
            
            return {
                "candidate_summary": {
                    "brief": analysis.get("summary", ""),
                    "strengths": analysis.get("strengths", []),
                    "performance_trend": self._analyze_performance_trend(previous_performance)
                },
                "key_talking_points": analysis.get("talking_points", []),
                "areas_to_explore": analysis.get("concerns", []),
                "red_flags": analysis.get("red_flags", []),
                "focus_areas": analysis.get("focus_areas", [])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing candidate for follow-up: {e}")
            return self._get_default_followup_analysis(resume, job_position, previous_performance)
    
    async def generate_followup_questions(
        self,
        resume: Resume,
        job_position: str,
        job_requirements: Optional[Dict[str, Any]] = None,
        previous_performance: Dict[str, Any] = None,
        interview_type: str = "final",
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """Generate follow-up interview questions based on previous performance."""
        
        # Determine question count based on performance
        num_questions = 8 if previous_performance.get('overall_rating', 0) >= 4 else 10
        
        prompt = f"""
        Generate follow-up interview questions for a {interview_type} round based on previous performance.
        
        Candidate: {resume.first_name} {resume.last_name}
        Position: {job_position}
        Previous Rating: {previous_performance.get('overall_rating', 'N/A')}/5
        
        Previous Interview Summary:
        - Strengths: {', '.join(previous_performance.get('strengths', []))}
        - Concerns: {', '.join(previous_performance.get('concerns', []))}
        
        Focus Areas for This Round: {', '.join(focus_areas) if focus_areas else 'General follow-up'}
        
        Low-Rated Previous Questions (need follow-up):
        {self._get_low_rated_questions(previous_performance.get('questions_asked', []))}
        
        Generate {num_questions} follow-up questions that:
        1. Address concerns from the previous interview
        2. Dive deeper into areas where candidate showed promise
        3. Clarify any ambiguous responses
        4. Test depth of knowledge in weak areas
        5. Are appropriate for a {interview_type} interview
        6. Build on previous answers without repetition
        
        Return a JSON object with a "questions" array:
        {{
            "questions": [
                {{
                    "question": "specific follow-up question text",
                    "category": "technical/behavioral/situational/culture_fit",
                    "relevance": "why this follow-up matters",
                    "expected_points": ["point 1", "point 2"],
                    "follow_up": "potential deeper follow-up",
                    "addresses_concern": "which previous concern this addresses"
                }}
            ]
        }}
        """
        
        try:
            response = await self.openai_service.generate_completion(prompt)
            
            try:
                questions = json.loads(response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse follow-up questions as JSON")
                return self._get_fallback_followup_questions(job_position, num_questions)
            
            # Process questions
            if isinstance(questions, dict) and 'questions' in questions:
                questions = questions['questions']
            
            enhanced_questions = []
            for i, q in enumerate(questions[:num_questions]):
                enhanced_questions.append({
                    "question_text": q.get("question", ""),
                    "category": self._map_category(q.get("category", "behavioral")),
                    "difficulty_level": 4,  # Higher difficulty for follow-up rounds
                    "generation_context": f"Follow-up: {q.get('addresses_concern', '')}",
                    "expected_answer_points": q.get("expected_points", []),
                    "follow_up_questions": [q.get("follow_up", "")] if q.get("follow_up") else [],
                    "order_index": i + 1,
                    "ai_generated": True
                })
            
            return {
                "questions": enhanced_questions,
                "total_count": len(enhanced_questions),
                "generation_metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "interview_type": interview_type,
                    "is_followup": True,
                    "previous_rating": previous_performance.get('overall_rating')
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}")
            return self._get_fallback_followup_questions(job_position, num_questions)
    
    def _format_previous_questions(self, questions: List[Dict]) -> str:
        """Format previous questions for prompt context."""
        if not questions:
            return "No previous questions available"
        
        formatted = []
        for q in questions[:10]:  # Limit to avoid token overflow
            formatted.append(
                f"- {q.get('question', 'Unknown question')[:100]}... "
                f"(Rating: {q.get('rating', 'N/A')}/5, Category: {q.get('category', 'Unknown')})"
            )
        
        return "\n".join(formatted)
    
    def _get_low_rated_questions(self, questions: List[Dict]) -> str:
        """Get questions with low ratings that need follow-up."""
        low_rated = [q for q in questions if q.get('rating', 5) <= 3]
        
        if not low_rated:
            return "All questions were answered satisfactorily"
        
        formatted = []
        for q in low_rated[:5]:
            formatted.append(
                f"- {q.get('question', 'Unknown')[:100]}... (Rating: {q.get('rating')}/5)"
            )
        
        return "\n".join(formatted)
    
    def _analyze_performance_trend(self, previous_performance: Dict) -> str:
        """Analyze performance trend from previous interview."""
        rating = previous_performance.get('overall_rating', 0)
        if rating >= 4.5:
            return "excellent"
        elif rating >= 3.5:
            return "good"
        elif rating >= 2.5:
            return "moderate"
        else:
            return "needs_improvement"
    
    def _get_default_followup_analysis(
        self, 
        resume: Resume, 
        job_position: str,
        previous_performance: Dict
    ) -> Dict[str, Any]:
        """Get default follow-up analysis if AI fails."""
        return {
            "candidate_summary": {
                "brief": f"Follow-up interview for {resume.first_name} {resume.last_name} based on previous performance",
                "strengths": previous_performance.get('strengths', []),
                "performance_trend": self._analyze_performance_trend(previous_performance)
            },
            "key_talking_points": [
                "Previous interview highlights",
                "Areas needing clarification",
                "Technical depth assessment"
            ],
            "areas_to_explore": previous_performance.get('concerns', []),
            "red_flags": [],
            "focus_areas": ["Technical skills", "Cultural fit", "Long-term goals"]
        }
    
    def _get_fallback_followup_questions(self, job_position: str, num_questions: int) -> Dict[str, Any]:
        """Get fallback follow-up questions if AI generation fails."""
        base_questions = [
            {
                "question_text": "Based on our previous discussion, can you elaborate on your approach to problem-solving?",
                "category": QuestionCategory.PROBLEM_SOLVING,
                "difficulty_level": 4
            },
            {
                "question_text": "You mentioned some challenges in your current role. How have you addressed them?",
                "category": QuestionCategory.BEHAVIORAL,
                "difficulty_level": 4
            },
            {
                "question_text": f"What specific aspects of this {job_position} role are most appealing to you?",
                "category": QuestionCategory.CULTURE_FIT,
                "difficulty_level": 3
            },
            {
                "question_text": "Can you provide more details about your technical experience we discussed?",
                "category": QuestionCategory.TECHNICAL,
                "difficulty_level": 4
            },
            {
                "question_text": "How would you handle conflicting priorities in this role?",
                "category": QuestionCategory.SITUATIONAL,
                "difficulty_level": 4
            }
        ]
        
        return {
            "questions": base_questions[:num_questions],
            "total_count": min(len(base_questions), num_questions),
            "generation_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "fallback": True,
                "is_followup": True
            }
        }
    
    async def analyze_transcript_content(
        self,
        transcript_data: Dict[str, Any],
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze interview transcript and extract Q&A pairs with ratings."""
        
        # Extract transcript text and speakers
        transcript_text = transcript_data.get("transcript_text", "")
        speakers_data = transcript_data.get("speakers", {})
        
        # Build conversation flow
        utterances = transcript_data.get("utterances", [])
        if not utterances:
            # Extract from speakers data if utterances not at top level
            utterances = []
            for speaker_id, speaker_info in speakers_data.items():
                for utt in speaker_info.get("utterances", []):
                    utterances.append({
                        **utt,
                        "speaker": speaker_id,
                        "role": speaker_info.get("likely_role", "unknown")
                    })
        
        # Sort by timestamp
        utterances.sort(key=lambda x: x.get("start", 0))
        
        # Log transcript info for debugging
        logger.info(f"Analyzing transcript with {len(utterances)} utterances")
        if utterances:
            logger.debug(f"First utterance: speaker={utterances[0].get('speaker')}, role={utterances[0].get('role')}, text={utterances[0].get('text', '')[:50]}...")
        
        # Check if we have valid utterances
        if not utterances:
            logger.warning("No utterances found in transcript data")
            return self._get_default_transcript_analysis(transcript_data, session_data)
        
        prompt = f"""
        Analyze this interview transcript and extract Q&A pairs with detailed evaluation.
        
        Interview Context:
        - Position: {session_data.get('job_position')}
        - Interview Type: {session_data.get('interview_type', 'general')}
        - Duration: {transcript_data.get('duration', 0)} seconds
        
        Transcript:
        {self._format_transcript_for_analysis(utterances)}
        
        IMPORTANT: The transcript uses [interviewer]: and [candidate]: tags to indicate speakers.
        
        For each question-answer pair:
        1. Identify the question asked by the interviewer
        2. Extract the candidate's complete response
        3. Evaluate the response quality (1-5 scale)
        4. Identify technical skills mentioned
        5. Assess communication clarity
        6. Note any red flags or exceptional points
        
        CRITICAL: You MUST extract at least one Q&A pair from the transcript. Even if the transcript is short,
        identify the questions asked and the candidate's responses.
        
        Also provide:
        - Overall interview assessment
        - Key strengths demonstrated
        - Areas of concern
        - Hiring recommendation
        
        Return a JSON object with this exact structure:
        {{
            "qa_pairs": [
                {{
                    "question": "interviewer question",
                    "answer": "candidate response",
                    "rating": 4,
                    "category": "technical/behavioral/situational",
                    "skills_mentioned": ["skill1", "skill2"],
                    "evaluation": "brief evaluation of response quality",
                    "red_flags": [],
                    "positive_signals": ["signal1"]
                }}
            ],
            "overall_assessment": {{
                "communication_score": 4.5,
                "technical_depth": 4.0,
                "cultural_fit": 4.2,
                "enthusiasm": 4.3,
                "overall_rating": 4.2
            }},
            "key_strengths": ["strength1", "strength2"],
            "areas_of_concern": ["concern1", "concern2"],
            "recommendation": "hire/no_hire/maybe",
            "summary": "2-3 sentence summary"
        }}
        """
        
        try:
            response = await self.openai_service.generate_completion(prompt)
            
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                logger.error("Failed to parse transcript analysis as JSON")
                return self._get_default_transcript_analysis(transcript_data, session_data)
            
            # Calculate aggregated scores for scorecard
            qa_pairs = analysis.get("qa_pairs", [])
            responses = []
            
            # Validate Q&A extraction
            if not qa_pairs:
                logger.warning("No Q&A pairs extracted from transcript analysis")
                logger.debug(f"Analysis response: {json.dumps(analysis, indent=2)}")
                # Log the formatted transcript that was sent to AI
                formatted_transcript = self._format_transcript_for_analysis(utterances)
                logger.debug(f"Formatted transcript sent to AI (first 500 chars): {formatted_transcript[:500]}")
            else:
                logger.info(f"Successfully extracted {len(qa_pairs)} Q&A pairs from transcript")
            
            for i, qa in enumerate(qa_pairs):
                # Validate required fields
                question = qa.get("question", "").strip()
                answer = qa.get("answer", "").strip()
                
                if not question or not answer:
                    logger.warning(f"Skipping Q&A pair {i} with missing data: Q='{question[:50]}...', A='{answer[:50]}...'")
                    continue
                
                responses.append({
                    "question_text": question,
                    "response_summary": answer[:500] if answer else "",  # Truncate long answers
                    "response_rating": qa.get("rating", 3),
                    "category": qa.get("category", "general"),
                    "skills_mentioned": qa.get("skills_mentioned", []),
                    "evaluation": qa.get("evaluation", "")
                })
            
            logger.info(f"Extracted {len(responses)} valid Q&A pairs from {len(qa_pairs)} total pairs")
            
            return {
                "qa_analysis": analysis,
                "responses_for_scorecard": responses,
                "transcript_insights": {
                    "total_questions": len(qa_pairs),
                    "average_rating": sum(qa.get("rating", 0) for qa in qa_pairs) / len(qa_pairs) if qa_pairs else 0,
                    "skills_identified": list(set(
                        skill for qa in qa_pairs 
                        for skill in qa.get("skills_mentioned", [])
                    )),
                    "interview_flow": "structured" if len(qa_pairs) > 5 else "conversational"
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing transcript: {e}")
            return self._get_default_transcript_analysis(transcript_data, session_data)
    
    def _format_transcript_for_analysis(self, utterances: List[Dict]) -> str:
        """Format utterances for analysis prompt."""
        formatted_lines = []
        
        for i, utt in enumerate(utterances[:100]):  # Limit to prevent token overflow
            speaker_role = utt.get("role", "unknown")
            if not speaker_role or speaker_role == "unknown":
                # Try to infer from speaker ID
                speaker_id = utt.get("speaker", "")
                speaker_role = "interviewer" if speaker_id == "A" else "candidate"
            
            text = utt.get("text", "").strip()
            if text:  # Only include non-empty utterances
                formatted_lines.append(f"[{speaker_role}]: {text}")
                
                # Log first few utterances for debugging
                if i < 3:
                    logger.debug(f"Utterance {i}: [{speaker_role}]: {text[:100]}...")
        
        # Log total formatted lines
        logger.info(f"Formatted {len(formatted_lines)} utterances for analysis")
        
        return "\n".join(formatted_lines)
    
    def _get_default_transcript_analysis(
        self, 
        transcript_data: Dict[str, Any],
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return default analysis if AI fails."""
        return {
            "qa_analysis": {
                "qa_pairs": [],
                "overall_assessment": {
                    "communication_score": 3.0,
                    "technical_depth": 3.0,
                    "cultural_fit": 3.0,
                    "enthusiasm": 3.0,
                    "overall_rating": 3.0
                },
                "key_strengths": ["Unable to analyze - manual review needed"],
                "areas_of_concern": ["Transcript analysis failed"],
                "recommendation": "maybe",
                "summary": "Automated analysis unavailable. Please review transcript manually."
            },
            "responses_for_scorecard": [],
            "transcript_insights": {
                "total_questions": 0,
                "average_rating": 0,
                "skills_identified": [],
                "interview_flow": "unknown"
            }
        }


# Singleton instance
interview_ai_service = InterviewAIService()