"""Service for handling candidate submissions."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import secrets

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

from app.models.submission import (
    CandidateSubmission, 
    InvitationCampaign, 
    SubmissionType, 
    SubmissionStatus
)
from app.models.resume import Resume
from app.models.user import User
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionSubmit,
    CampaignCreate,
    CampaignUpdate
)
from app.services.email_service_production import email_service
from app.services.resume_parser import ResumeParser
from app.core.config import settings

logger = logging.getLogger(__name__)


class SubmissionService:
    """Handle candidate submission operations."""
    
    async def create_submission(
        self,
        db: AsyncSession,
        recruiter_id: UUID,
        data: SubmissionCreate
    ) -> CandidateSubmission:
        """Create a new submission invitation."""
        # Generate secure token
        token = self._generate_secure_token()
        
        # Create submission
        submission = CandidateSubmission(
            token=token,
            submission_type=data.submission_type.value,  # Convert enum to string value
            recruiter_id=recruiter_id,
            email=data.email,
            resume_id=data.resume_id or data.candidate_id,  # Use either resume_id or candidate_id
            campaign_id=data.campaign_id,
            expires_at=datetime.utcnow() + timedelta(days=data.expires_in_days)
        )
        
        # Set candidate name if provided
        if data.candidate_name:
            name_parts = data.candidate_name.split()
            submission.first_name = name_parts[0] if name_parts else None
            submission.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
        
        # If updating existing resume, copy current data
        if data.submission_type == SubmissionType.UPDATE and data.resume_id:
            resume = await db.get(Resume, data.resume_id)
            if resume and resume.user_id == recruiter_id:
                submission.email = submission.email or resume.email
                submission.first_name = resume.first_name
                submission.last_name = resume.last_name
        
        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        
        # Send invitation email with custom message if provided
        try:
            await self._send_invitation_email(db, submission, custom_message=data.message)
        except Exception as e:
            logger.error(f"Failed to send invitation email: {e}")
            logger.error(f"Submission data: id={submission.id}, expires_at={getattr(submission, 'expires_at', 'NOT SET')}")
            # Don't fail the whole operation if email fails
        
        return submission
    
    async def create_bulk_submissions(
        self,
        db: AsyncSession,
        recruiter_id: UUID,
        emails: List[str],
        submission_type: SubmissionType,
        campaign_id: Optional[UUID] = None,
        expires_in_days: int = 7
    ) -> Dict[str, Any]:
        """Create bulk submission invitations."""
        results = {
            "total": len(emails),
            "successful": 0,
            "failed": 0,
            "submissions": [],
            "errors": []
        }
        
        for email in emails:
            try:
                # Check if candidate already exists
                existing = await db.execute(
                    select(Resume).where(
                        and_(
                            Resume.email == email,
                            Resume.user_id == recruiter_id,
                            Resume.status == "active"
                        )
                    )
                )
                existing_resume = existing.scalar_one_or_none()
                
                # Create submission
                submission_data = SubmissionCreate(
                    submission_type=submission_type if not existing_resume else SubmissionType.UPDATE,
                    email=email,
                    resume_id=existing_resume.id if existing_resume else None,
                    campaign_id=campaign_id,
                    expires_in_days=expires_in_days
                )
                
                submission = await self.create_submission(db, recruiter_id, submission_data)
                results["submissions"].append(submission)
                results["successful"] += 1
                
            except Exception as e:
                logger.error(f"Error creating submission for {email}: {e}")
                results["errors"].append({"email": email, "error": str(e)})
                results["failed"] += 1
        
        return results
    
    async def get_submission_by_token(
        self,
        db: AsyncSession,
        token: str,
        include_campaign: bool = False
    ) -> Optional[CandidateSubmission]:
        """Get submission by token."""
        query = select(CandidateSubmission).where(CandidateSubmission.token == token)
        
        if include_campaign:
            query = query.options(selectinload(CandidateSubmission.campaign))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def submit_candidate_data(
        self,
        db: AsyncSession,
        token: str,
        data: SubmissionSubmit
    ) -> CandidateSubmission:
        """Process candidate submission."""
        # Get submission
        submission = await self.get_submission_by_token(db, token)
        if not submission:
            raise ValueError("Invalid submission token")
        
        # Check if expired
        if submission.is_expired:
            submission.status = SubmissionStatus.EXPIRED.value  # Convert to string
            await db.commit()
            raise ValueError("Submission link has expired")
        
        # Check if already submitted
        if submission.status != SubmissionStatus.PENDING.value:  # Compare with string value
            raise ValueError("This submission has already been processed. Each submission link can only be used once.")
        
        # Validate that at least basic information is provided
        if not data.email and not submission.email:
            raise ValueError("Email address is required")
        
        if not data.first_name and not submission.first_name:
            raise ValueError("First name is required")
        
        if not data.last_name and not submission.last_name:
            raise ValueError("Last name is required")
        
        # Update submission data
        submission.email = data.email or submission.email
        submission.first_name = data.first_name
        submission.last_name = data.last_name
        submission.phone = data.phone
        submission.linkedin_url = str(data.linkedin_url) if data.linkedin_url else None
        submission.availability = data.availability
        submission.salary_expectations = data.salary_expectations
        submission.location_preferences = data.location_preferences
        
        # Process resume if provided
        if data.resume_file or data.resume_text:
            parsed_data = await self._parse_resume(
                data.resume_file, 
                data.resume_text,
                data.resume_filename
            )
            submission.parsed_data = parsed_data
            submission.resume_text = data.resume_text or parsed_data.get("text", "")
            # Store the filename if provided
            if data.resume_filename:
                submission.resume_file_url = data.resume_filename  # Store filename for reference
        else:
            # No resume provided - set empty values
            submission.parsed_data = {}
            submission.resume_text = ""
        
        # Update status
        submission.status = SubmissionStatus.SUBMITTED.value  # Convert to string
        submission.submitted_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(submission)
        
        # Process into resume database
        await self._process_submission(db, submission)
        
        # Notify recruiter
        await self._notify_recruiter(db, submission)
        
        return submission
    
    async def create_campaign(
        self,
        db: AsyncSession,
        recruiter_id: UUID,
        data: CampaignCreate
    ) -> InvitationCampaign:
        """Create a new invitation campaign."""
        campaign = InvitationCampaign(
            recruiter_id=recruiter_id,
            **data.dict()
        )
        
        # Generate public slug if public
        if data.is_public:
            campaign.public_slug = campaign.generate_public_slug()
        
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        
        return campaign
    
    async def update_campaign(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        recruiter_id: UUID,
        data: CampaignUpdate
    ) -> InvitationCampaign:
        """Update an existing campaign."""
        campaign = await db.get(InvitationCampaign, campaign_id)
        if not campaign or campaign.recruiter_id != recruiter_id:
            raise ValueError("Campaign not found")
        
        # Update fields
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)
        
        # Generate slug if making public
        if data.is_public and not campaign.public_slug:
            campaign.public_slug = campaign.generate_public_slug()
        
        await db.commit()
        await db.refresh(campaign)
        
        return campaign
    
    async def get_recruiter_campaigns(
        self,
        db: AsyncSession,
        recruiter_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[InvitationCampaign]:
        """Get all campaigns for a recruiter."""
        result = await db.execute(
            select(InvitationCampaign)
            .where(InvitationCampaign.recruiter_id == recruiter_id)
            .order_by(InvitationCampaign.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_campaign_by_slug(
        self,
        db: AsyncSession,
        slug: str
    ) -> Optional[InvitationCampaign]:
        """Get public campaign by slug."""
        result = await db.execute(
            select(InvitationCampaign).where(
                and_(
                    InvitationCampaign.public_slug == slug,
                    InvitationCampaign.is_public == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_submission_analytics(
        self,
        db: AsyncSession,
        recruiter_id: UUID,
        campaign_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get analytics for submissions."""
        query = select(CandidateSubmission).where(
            CandidateSubmission.recruiter_id == recruiter_id
        )
        
        if campaign_id:
            query = query.where(CandidateSubmission.campaign_id == campaign_id)
        
        result = await db.execute(query)
        submissions = result.scalars().all()
        
        # Calculate analytics
        analytics = {
            "total_sent": len(submissions),
            "total_opened": sum(1 for s in submissions if s.email_opened_at),
            "total_clicked": sum(1 for s in submissions if s.link_clicked_at),
            "total_submitted": sum(1 for s in submissions if s.status == SubmissionStatus.SUBMITTED.value),  # Compare with string
            "total_processed": sum(1 for s in submissions if s.status == SubmissionStatus.PROCESSED.value),  # Compare with string
            "by_status": {},
            "by_type": {}
        }
        
        # Group by status
        for status in SubmissionStatus:
            count = sum(1 for s in submissions if s.status == status.value)  # Compare with string value
            analytics["by_status"][status.value] = count
        
        # Group by type
        for sub_type in SubmissionType:
            count = sum(1 for s in submissions if s.submission_type == sub_type.value)  # Compare with string value
            analytics["by_type"][sub_type.value] = count
        
        # Calculate conversion rate
        if analytics["total_sent"] > 0:
            analytics["conversion_rate"] = analytics["total_submitted"] / analytics["total_sent"]
        else:
            analytics["conversion_rate"] = 0.0
        
        # Calculate average time to submit
        submit_times = []
        for s in submissions:
            if s.submitted_at and s.created_at:
                delta = (s.submitted_at - s.created_at).total_seconds() / 3600  # hours
                submit_times.append(delta)
        
        if submit_times:
            analytics["average_time_to_submit"] = sum(submit_times) / len(submit_times)
        
        return analytics
    
    # Private methods
    def _generate_secure_token(self) -> str:
        """Generate a secure token for submissions."""
        return f"sub_{secrets.token_urlsafe(32)}"
    
    async def _send_invitation_email(
        self,
        db: AsyncSession,
        submission: CandidateSubmission,
        custom_message: Optional[str] = None
    ):
        """Send invitation email to candidate."""
        try:
            # Get recruiter info
            recruiter = await db.get(User, submission.recruiter_id)
            
            # Calculate deadline days
            deadline_days = (submission.expires_at - datetime.utcnow()).days
            
            # Use custom message if provided, otherwise use default
            if custom_message:
                message = custom_message
            elif submission.submission_type == SubmissionType.UPDATE.value:
                message = "We'd like to ensure we have your most current information on file. Please take a few minutes to update your profile."
            else:
                message = "We're building a talent pool for exciting opportunities and would love to have your profile on file."
            
            # Format candidate name properly
            if submission.first_name and submission.last_name:
                candidate_name = f"{submission.first_name} {submission.last_name}"
            elif submission.first_name:
                candidate_name = submission.first_name
            elif submission.last_name:
                candidate_name = submission.last_name
            else:
                # Extract name from email if no name provided
                email_username = submission.email.split('@')[0]
                candidate_name = email_username.replace('.', ' ').replace('_', ' ').title()
            
            import sys
            print(f"\n[SUBMISSION SERVICE] Sending invitation email to: {submission.email}", flush=True)
            print(f"[SUBMISSION SERVICE] Submission link: {submission.submission_url}", flush=True)
            print(f"[SUBMISSION SERVICE] Email service type: {type(email_service).__name__}", flush=True)
            print(f"[SUBMISSION SERVICE] Email service module: {email_service.__module__}", flush=True)
            sys.stdout.flush()
            
            # Send email with correct parameters
            # Ensure company name is never None
            company_name = "Promtitude"
            if recruiter and recruiter.company:
                company_name = recruiter.company
            
            result = await email_service.send_submission_invitation(
                to_email=submission.email,
                candidate_name=candidate_name,
                recruiter_name=recruiter.full_name if recruiter else "Our team",
                submission_link=submission.submission_url,
                message=message,
                deadline_days=deadline_days,
                company_name=company_name,
                is_update=(submission.submission_type == SubmissionType.UPDATE.value),
                expires_at=submission.expires_at
            )
            
            print(f"[SUBMISSION SERVICE] Email send result: {result}")
            
            # Update email sent timestamp
            submission.email_sent_at = datetime.utcnow()
            await db.commit()
            
        except Exception as e:
            print(f"[SUBMISSION SERVICE] Error sending email: {e}")
            logger.error(f"Error sending invitation email: {e}")
    
    async def _parse_resume(
        self,
        resume_file: Optional[str],
        resume_text: Optional[str],
        resume_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Parse resume data."""
        parser = ResumeParser()
        extracted_text = ""
        
        if resume_file:
            try:
                # Decode base64 file content
                import base64
                from app.services.file_parser import FileParser
                
                # Remove data URL prefix if present
                if ',' in resume_file:
                    resume_file = resume_file.split(',')[1]
                
                # Decode base64 to bytes
                file_content = base64.b64decode(resume_file)
                
                # Use FileParser to extract text based on file type
                if resume_filename:
                    # FileParser.extract_text uses filename to determine format
                    try:
                        extracted_text = FileParser.extract_text(file_content, resume_filename)
                        logger.info(f"Successfully extracted {len(extracted_text)} characters from {resume_filename}")
                    except Exception as e:
                        logger.error(f"Error extracting text from {resume_filename}: {e}")
                else:
                    # Fallback to PDF if no filename provided
                    try:
                        extracted_text = FileParser.extract_text_from_pdf(file_content)
                        logger.info(f"Successfully extracted {len(extracted_text)} characters from uploaded file (assumed PDF)")
                    except Exception as pdf_error:
                        logger.warning(f"PDF parsing failed: {pdf_error}")
                
            except Exception as e:
                logger.error(f"Error parsing uploaded file: {e}")
                # Continue with text parsing if file parsing fails
        
        # Parse either the extracted text from file or the provided text
        text_to_parse = extracted_text or resume_text
        
        if text_to_parse:
            parsed_data = await parser.parse_resume(text_to_parse)
            # Include the extracted text in the parsed data
            if extracted_text and not resume_text:
                parsed_data['text'] = extracted_text
            return parsed_data
        
        return {}
    
    async def _process_submission(
        self,
        db: AsyncSession,
        submission: CandidateSubmission
    ):
        """Process submission into resume database."""
        try:
            if submission.submission_type == SubmissionType.UPDATE:
                # Update existing resume
                if submission.resume_id:
                    resume = await db.get(Resume, submission.resume_id)
                    if resume:
                        # Update fields
                        resume.email = submission.email or resume.email
                        resume.phone = submission.phone or resume.phone
                        # Handle linkedin_url - set to None if empty string
                        if submission.linkedin_url:
                            resume.linkedin_url = submission.linkedin_url
                        elif submission.linkedin_url == "":
                            resume.linkedin_url = None
                        
                        # Update resume content if provided
                        if submission.resume_text:
                            resume.raw_text = submission.resume_text
                        
                        # Update parsed data if available
                        if submission.parsed_data:
                            resume.parsed_data = {**resume.parsed_data, **submission.parsed_data}
                            resume.skills = submission.parsed_data.get("skills", resume.skills)
                            resume.summary = submission.parsed_data.get("summary", resume.summary)
                            resume.current_title = submission.parsed_data.get("current_title", resume.current_title)
                            resume.years_experience = submission.parsed_data.get("years_experience", resume.years_experience)
                        
                        # Update name if provided
                        if submission.first_name:
                            resume.first_name = submission.first_name
                        if submission.last_name:
                            resume.last_name = submission.last_name
                        
                        resume.updated_at = datetime.utcnow()
            else:
                # Check if a resume with this email already exists for this recruiter
                from sqlalchemy import and_, select
                existing_resume_query = await db.execute(
                    select(Resume).where(
                        and_(
                            Resume.user_id == submission.recruiter_id,
                            Resume.email == submission.email,
                            Resume.status == "active"
                        )
                    )
                )
                existing_resume = existing_resume_query.scalar_one_or_none()
                
                if existing_resume:
                    # Update existing resume instead of creating a new one
                    logger.info(f"Found existing resume for email {submission.email}, updating instead of creating new")
                    logger.info(f"Existing resume ID: {existing_resume.id}, Name: {existing_resume.first_name} {existing_resume.last_name}")
                    
                    # Update existing resume fields
                    existing_resume.first_name = submission.first_name or existing_resume.first_name
                    existing_resume.last_name = submission.last_name or existing_resume.last_name
                    existing_resume.phone = submission.phone or existing_resume.phone
                    
                    # Handle linkedin_url
                    if submission.linkedin_url:
                        existing_resume.linkedin_url = submission.linkedin_url
                    elif submission.linkedin_url == "":
                        existing_resume.linkedin_url = None
                    
                    # Update resume content if provided
                    if submission.resume_text:
                        existing_resume.raw_text = submission.resume_text
                    
                    # Update parsed data if available
                    if submission.parsed_data:
                        existing_resume.parsed_data = {**existing_resume.parsed_data, **submission.parsed_data}
                        existing_resume.skills = submission.parsed_data.get("skills", existing_resume.skills)
                        existing_resume.summary = submission.parsed_data.get("summary", existing_resume.summary)
                        existing_resume.current_title = submission.parsed_data.get("current_title", existing_resume.current_title)
                        existing_resume.years_experience = submission.parsed_data.get("years_experience", existing_resume.years_experience)
                    
                    # Update location if provided
                    if submission.location_preferences:
                        locations = submission.location_preferences.get("locations", [])
                        if locations:
                            existing_resume.location = ", ".join(locations)
                    
                    existing_resume.updated_at = datetime.utcnow()
                    resume = existing_resume
                else:
                    # Create new resume only if it doesn't exist
                    # Extract location from location preferences if available
                    location = ""
                    if submission.location_preferences:
                        locations = submission.location_preferences.get("locations", [])
                        if locations:
                            location = ", ".join(locations)
                    
                    resume = Resume(
                        user_id=submission.recruiter_id,
                        first_name=submission.first_name,
                        last_name=submission.last_name,
                        email=submission.email,
                        phone=submission.phone or "",
                        location=location or None,  # Set to None if empty
                        linkedin_url=submission.linkedin_url or None,  # Set to None instead of empty string
                        parsed_data=submission.parsed_data or {},
                        raw_text=submission.resume_text or "",  # Empty string if no resume
                        skills=submission.parsed_data.get("skills", []) if submission.parsed_data else [],
                        current_title=submission.parsed_data.get("current_title", "") if submission.parsed_data else "",
                        summary=submission.parsed_data.get("summary", "") if submission.parsed_data else "",
                        years_experience=submission.parsed_data.get("years_experience", 0) if submission.parsed_data else 0,
                        # Set parse status to completed since there's nothing to parse if no resume
                        parse_status="completed" if not submission.resume_text else "pending",
                        # Explicitly set status to active
                        status="active"
                    )
                    db.add(resume)
            
            # Update submission status
            submission.status = SubmissionStatus.PROCESSED.value  # Convert to string
            submission.processed_at = datetime.utcnow()
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error processing submission: {e}")
            logger.error(f"Submission data: id={submission.id}, first_name={submission.first_name}, last_name={submission.last_name}, email={submission.email}")
            logger.error(f"Resume text length: {len(submission.resume_text) if submission.resume_text else 0}")
            # Rollback the transaction to prevent the "transaction has been rolled back" error
            await db.rollback()
            raise  # Re-raise the exception to see the actual error
    
    async def _notify_recruiter(
        self,
        db: AsyncSession,
        submission: CandidateSubmission
    ):
        """Notify recruiter of new submission."""
        try:
            recruiter = await db.get(User, submission.recruiter_id)
            if recruiter and recruiter.email:
                await email_service.send_submission_notification(
                    to_email=recruiter.email,
                    candidate_name=f"{submission.first_name} {submission.last_name}",
                    submission_type=submission.submission_type  # Already a string, not an enum
                )
        except Exception as e:
            logger.error(f"Error notifying recruiter: {e}")


# Singleton instance
submission_service = SubmissionService()