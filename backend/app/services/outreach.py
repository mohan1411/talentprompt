"""Outreach message generation service."""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Resume, OutreachMessage, MessageStyle, MessageStatus
from app.services.openai import OpenAIService
from app.core.config import settings

logger = logging.getLogger(__name__)


class OutreachService:
    """Service for generating personalized outreach messages."""
    
    def __init__(self):
        self.openai = OpenAIService()
    
    async def generate_messages(
        self,
        db: AsyncSession,
        user_id: UUID,
        resume_id: UUID,
        job_title: str,
        company_name: Optional[str] = None,
        job_requirements: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate personalized outreach messages for a candidate.
        
        Args:
            db: Database session
            user_id: ID of the user generating the message
            resume_id: ID of the target candidate's resume
            job_title: Title of the position to recruit for
            company_name: Name of the hiring company
            job_requirements: Dict with skills, experience, etc.
            custom_instructions: Additional instructions for message generation
        
        Returns:
            Dict containing generated messages in different styles
        """
        try:
            # Fetch candidate data
            result = await db.execute(
                select(Resume).where(Resume.id == resume_id)
            )
            resume = result.scalar_one_or_none()
            
            if not resume:
                raise ValueError(f"Resume {resume_id} not found")
            
            # Extract candidate information
            candidate_info = self._extract_candidate_info(resume)
            
            # Generate messages in different styles
            messages = {}
            for style in [MessageStyle.CASUAL, MessageStyle.PROFESSIONAL, MessageStyle.TECHNICAL]:
                message_data = await self._generate_message(
                    candidate_info=candidate_info,
                    job_title=job_title,
                    company_name=company_name,
                    job_requirements=job_requirements,
                    style=style,
                    custom_instructions=custom_instructions
                )
                
                # Save to database
                outreach_message = OutreachMessage(
                    user_id=user_id,
                    resume_id=resume_id,
                    subject=message_data["subject"],
                    body=message_data["body"],
                    style=style.value,  # Use the enum value (lowercase)
                    job_title=job_title,
                    job_requirements=job_requirements,
                    company_name=company_name,
                    status=MessageStatus.GENERATED.value,  # Use the enum value
                    quality_score=message_data.get("quality_score", 0.8),
                    generation_prompt=message_data.get("prompt"),
                    model_version=settings.OPENAI_MODEL
                )
                db.add(outreach_message)
                
                messages[style.value] = {
                    "subject": message_data["subject"],
                    "body": message_data["body"],
                    "quality_score": message_data.get("quality_score", 0.8)
                }
            
            await db.commit()
            
            return {
                "success": True,
                "messages": messages,
                "candidate_name": candidate_info["name"],
                "candidate_title": candidate_info["current_title"]
            }
            
        except Exception as e:
            logger.error(f"Error generating outreach messages: {str(e)}")
            raise
    
    def _extract_candidate_info(self, resume: Resume) -> Dict[str, Any]:
        """Extract relevant candidate information from resume."""
        # Combine first and last name
        full_name = f"{resume.first_name} {resume.last_name}".strip()
        
        # Extract top skills (limit to 5 most relevant)
        top_skills = resume.skills[:5] if resume.skills else []
        
        # Get recent experience
        recent_experience = None
        if resume.parsed_data and "experience" in resume.parsed_data:
            experiences = resume.parsed_data["experience"]
            if experiences and len(experiences) > 0:
                recent_experience = experiences[0]
        
        return {
            "name": full_name,
            "current_title": resume.current_title or "Professional",
            "location": resume.location or "",
            "years_experience": resume.years_experience or 0,
            "top_skills": top_skills,
            "recent_company": recent_experience.get("company") if recent_experience else None,
            "recent_role": recent_experience.get("title") if recent_experience else resume.current_title,
            "summary": resume.summary or "",
            "linkedin_url": resume.linkedin_url or ""
        }
    
    async def _generate_message(
        self,
        candidate_info: Dict[str, Any],
        job_title: str,
        company_name: Optional[str],
        job_requirements: Optional[Dict[str, Any]],
        style: MessageStyle,
        custom_instructions: Optional[str]
    ) -> Dict[str, Any]:
        """Generate a single outreach message using GPT-4.1-mini."""
        
        # Build the prompt
        style_instructions = {
            MessageStyle.CASUAL: "Write in a friendly, conversational tone. Use informal language but remain professional.",
            MessageStyle.PROFESSIONAL: "Write in a formal, professional tone. Be respectful and business-oriented.",
            MessageStyle.TECHNICAL: "Write with technical depth. Reference specific technologies and demonstrate domain knowledge."
        }
        
        prompt = f"""Generate a personalized recruiting outreach message for the following candidate:

Candidate Information:
- Name: {candidate_info['name']}
- Current Role: {candidate_info['current_title']}
- Location: {candidate_info['location']}
- Years of Experience: {candidate_info['years_experience']}
- Top Skills: {', '.join(candidate_info['top_skills'])}
- Recent Company: {candidate_info['recent_company'] or 'Not specified'}

Position Details:
- Job Title: {job_title}
- Company: {company_name or 'Our company'}
- Requirements: {json.dumps(job_requirements) if job_requirements else 'Not specified'}

Writing Style: {style_instructions[style]}

{f"Additional Instructions: {custom_instructions}" if custom_instructions else ""}

Generate a message that:
1. Opens with something specific from their background (not generic)
2. Clearly explains why they're a good fit for this role
3. Provides a compelling reason to consider the opportunity
4. Includes a clear call-to-action
5. Is concise (under 150 words for the body)

Return the response in JSON format:
{{
    "subject": "Compelling subject line that mentions something specific",
    "body": "The message body",
    "quality_score": 0.0-1.0 based on how well it follows the guidelines
}}"""
        
        try:
            response = await self.openai.generate_completion(
                prompt=prompt,
                temperature=0.7,
                max_tokens=500,
                response_format="json"
            )
            
            message_data = json.loads(response)
            message_data["prompt"] = prompt  # Store for debugging
            
            return message_data
            
        except Exception as e:
            logger.error(f"Error generating message with style {style}: {str(e)}")
            # Fallback message
            return {
                "subject": f"Exciting {job_title} opportunity for you",
                "body": f"Hi {candidate_info['name']},\n\nI came across your profile and was impressed by your experience as {candidate_info['current_title']}. We have an exciting {job_title} opportunity that seems like a great match for your skills.\n\nWould you be open to a brief conversation?\n\nBest regards",
                "quality_score": 0.5,
                "prompt": prompt
            }
    
    async def get_message_templates(
        self,
        db: AsyncSession,
        user_id: Optional[UUID] = None,
        industry: Optional[str] = None,
        role_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get outreach templates based on filters."""
        # Implementation for retrieving templates
        # This would query the OutreachTemplate table
        pass
    
    async def track_message_performance(
        self,
        db: AsyncSession,
        message_id: UUID,
        event: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track performance metrics for outreach messages."""
        try:
            result = await db.execute(
                select(OutreachMessage).where(OutreachMessage.id == message_id)
            )
            message = result.scalar_one_or_none()
            
            if not message:
                return False
            
            if event == "sent":
                message.status = MessageStatus.SENT
                message.sent_at = datetime.utcnow()
            elif event == "opened":
                message.status = MessageStatus.OPENED
                message.opened_at = datetime.utcnow()
            elif event == "responded":
                message.status = MessageStatus.RESPONDED
                message.responded_at = datetime.utcnow()
                # Update response rate metrics
            
            await db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error tracking message performance: {str(e)}")
            return False