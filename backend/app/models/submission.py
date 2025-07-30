"""Candidate submission models."""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import enum

from app.db.base_class import Base


class SubmissionType(str, enum.Enum):
    """Types of candidate submissions."""
    UPDATE = "update"  # Update existing resume
    NEW = "new"       # New candidate submission


class SubmissionStatus(str, enum.Enum):
    """Status of a submission."""
    PENDING = "pending"      # Invitation sent, not submitted
    SUBMITTED = "submitted"  # Candidate submitted
    PROCESSED = "processed"  # Processed and added to resume database
    EXPIRED = "expired"      # Token expired
    CANCELLED = "cancelled"  # Cancelled by recruiter


class CandidateSubmission(Base):
    """Track candidate resume submissions via invitation links."""
    
    __tablename__ = "candidate_submissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(255), unique=True, nullable=False, index=True)
    submission_type = Column(String(10), nullable=False)  # Changed from Enum to String
    status = Column(String(20), default=SubmissionStatus.PENDING.value, nullable=False)  # Changed from Enum to String
    
    # Relationships
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("invitation_campaigns.id"), nullable=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True)  # For updates
    
    # Candidate info
    email = Column(String(255), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    
    # Submission data
    resume_file_url = Column(String(500), nullable=True)
    resume_text = Column(Text, nullable=True)
    parsed_data = Column(JSON, nullable=True)  # Structured data from resume
    
    # Additional info collected
    availability = Column(String(50), nullable=True)  # immediate, 1_month, 3_months, not_looking
    salary_expectations = Column(JSON, nullable=True)  # {min: 100000, max: 150000, currency: "USD"}
    location_preferences = Column(JSON, nullable=True)  # {remote: true, hybrid: true, onsite: false, locations: [...]}
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Email tracking
    email_sent_at = Column(DateTime, nullable=True)
    email_opened_at = Column(DateTime, nullable=True)
    link_clicked_at = Column(DateTime, nullable=True)
    
    # Relationships
    recruiter = relationship("User", backref="candidate_submissions")
    campaign = relationship("InvitationCampaign", backref="submissions")
    resume = relationship("Resume", backref="submission_updates")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.token:
            self.token = self.generate_token()
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(days=7)
    
    @staticmethod
    def generate_token():
        """Generate a secure token for the submission link."""
        return f"sub_{uuid.uuid4().hex}"
    
    @property
    def is_expired(self):
        """Check if the submission token has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def submission_url(self):
        """Get the full submission URL."""
        from app.core.config import settings
        return f"{settings.FRONTEND_URL}/submit/{self.token}"


class InvitationCampaign(Base):
    """Track invitation campaigns for bulk invites and analytics."""
    
    __tablename__ = "invitation_campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String(50), nullable=True)  # job_fair, referral, direct, etc.
    
    # For public/shareable links
    public_slug = Column(String(100), unique=True, nullable=True, index=True)
    is_public = Column(Boolean, default=False)
    
    # Customization
    email_template = Column(Text, nullable=True)  # Custom email message
    branding = Column(JSON, nullable=True)  # Logo URL, colors, etc.
    
    # Settings
    auto_close_date = Column(DateTime, nullable=True)  # Auto-close submissions after this date
    max_submissions = Column(Integer, nullable=True)  # Limit number of submissions
    
    # Analytics
    stats = Column(JSON, default=dict)  # {views: 0, submissions: 0, completion_rate: 0}
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    recruiter = relationship("User", backref="invitation_campaigns")
    
    @property
    def public_url(self):
        """Get the public submission URL if campaign is public."""
        if self.is_public and self.public_slug:
            from app.core.config import settings
            return f"{settings.FRONTEND_URL}/submit/campaign/{self.public_slug}"
        return None
    
    def generate_public_slug(self):
        """Generate a URL-friendly slug for public campaigns."""
        import re
        from app.core.security import get_random_string
        
        # Create slug from name
        slug_base = re.sub(r'[^\w\s-]', '', self.name.lower())
        slug_base = re.sub(r'[-\s]+', '-', slug_base)
        
        # Add random suffix for uniqueness
        return f"{slug_base[:50]}-{get_random_string(6)}"