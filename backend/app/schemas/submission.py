"""Schemas for candidate submissions."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, HttpUrl, Field, field_validator
from uuid import UUID

from app.models.submission import SubmissionType, SubmissionStatus


# Base schemas
class SubmissionBase(BaseModel):
    """Base schema for submissions."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None  # Changed from HttpUrl to str
    availability: Optional[str] = None
    salary_expectations: Optional[Dict[str, Any]] = None
    location_preferences: Optional[Dict[str, Any]] = None


class CampaignBase(BaseModel):
    """Base schema for invitation campaigns."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_type: Optional[str] = None
    is_public: bool = False
    email_template: Optional[str] = None
    branding: Optional[Dict[str, Any]] = None
    auto_close_date: Optional[datetime] = None
    max_submissions: Optional[int] = None


# Create schemas
class SubmissionCreate(BaseModel):
    """Schema for creating a new submission invitation."""
    submission_type: SubmissionType
    email: Optional[EmailStr] = None
    candidate_name: Optional[str] = None  # Add this field
    message: Optional[str] = None  # Add this field
    resume_id: Optional[UUID] = None  # For updates
    candidate_id: Optional[UUID] = None  # Alternative to resume_id
    campaign_id: Optional[UUID] = None
    expires_in_days: int = 7
    
    @field_validator('resume_id')
    @classmethod
    def validate_resume_id(cls, v, info):
        """Ensure resume_id is provided for updates."""
        if info.data.get('submission_type') == SubmissionType.UPDATE and not v:
            raise ValueError("resume_id is required for update submissions")
        return v


class SubmissionSubmit(BaseModel):
    """Schema for candidate submitting their information."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None  # Changed from HttpUrl to str
    availability: Optional[str] = None
    salary_expectations: Optional[Dict[str, Any]] = None
    location_preferences: Optional[Dict[str, Any]] = None
    resume_file: Optional[str] = None  # Base64 encoded file
    resume_text: Optional[str] = None
    
    @field_validator('linkedin_url')
    @classmethod
    def validate_linkedin_url(cls, v):
        """Validate LinkedIn URL format."""
        if v and v.strip():
            # Basic validation - just check if it contains linkedin
            if 'linkedin' not in v.lower() and not v.startswith('http'):
                # Prepend https:// if missing
                v = f"https://linkedin.com/in/{v}"
        return v
    
    @field_validator('resume_file')
    @classmethod
    def validate_resume_file(cls, v):
        """Validate resume file size and format."""
        if v:
            # TODO: Add file size validation
            # TODO: Add file format validation
            pass
        return v


class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign."""
    pass


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    email_template: Optional[str] = None
    branding: Optional[Dict[str, Any]] = None
    auto_close_date: Optional[datetime] = None
    max_submissions: Optional[int] = None


# Response schemas
class SubmissionResponse(SubmissionBase):
    """Response schema for submissions."""
    id: UUID
    token: str
    submission_type: SubmissionType
    status: SubmissionStatus
    recruiter_id: UUID
    campaign_id: Optional[UUID]
    resume_id: Optional[UUID]
    submission_url: str
    created_at: datetime
    expires_at: datetime
    submitted_at: Optional[datetime]
    processed_at: Optional[datetime]
    
    class Config:
        orm_mode = True
        from_attributes = True


class SubmissionPublicResponse(BaseModel):
    """Public response for submission status (for candidates)."""
    status: SubmissionStatus
    submission_type: SubmissionType
    expires_at: datetime
    recruiter_name: Optional[str] = None
    company_name: Optional[str] = None
    campaign_name: Optional[str] = None
    is_expired: bool
    
    class Config:
        orm_mode = True


class CampaignResponse(CampaignBase):
    """Response schema for campaigns."""
    id: UUID
    recruiter_id: UUID
    public_slug: Optional[str]
    public_url: Optional[str]
    stats: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    submission_count: int = 0
    
    class Config:
        orm_mode = True
        from_attributes = True


class CampaignPublicResponse(BaseModel):
    """Public response for campaigns (for candidates)."""
    name: str
    description: Optional[str]
    company_name: Optional[str]
    branding: Optional[Dict[str, Any]]
    is_open: bool
    
    class Config:
        orm_mode = True


# Bulk operations
class BulkInviteRequest(BaseModel):
    """Request for bulk invitations."""
    emails: List[EmailStr]
    submission_type: SubmissionType = SubmissionType.NEW
    campaign_id: Optional[UUID] = None
    email_template: Optional[str] = None
    expires_in_days: int = 7


class BulkInviteResponse(BaseModel):
    """Response for bulk invitations."""
    total: int
    successful: int
    failed: int
    submissions: List[SubmissionResponse]
    errors: List[Dict[str, str]] = []


# Analytics schemas
class SubmissionAnalytics(BaseModel):
    """Analytics for submissions."""
    total_sent: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_submitted: int = 0
    total_processed: int = 0
    conversion_rate: float = 0.0
    average_time_to_submit: Optional[float] = None
    by_status: Dict[str, int] = {}
    by_type: Dict[str, int] = {}


class CampaignAnalytics(BaseModel):
    """Analytics for a campaign."""
    campaign_id: UUID
    campaign_name: str
    total_invites: int = 0
    total_submissions: int = 0
    conversion_rate: float = 0.0
    by_source: Dict[str, int] = {}
    top_locations: List[Dict[str, Any]] = []
    salary_range: Optional[Dict[str, float]] = None