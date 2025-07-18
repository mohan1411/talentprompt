"""Outreach message schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import MessageStyle, MessageStatus


class OutreachMessageGenerate(BaseModel):
    """Request schema for generating outreach messages."""
    
    resume_id: UUID = Field(..., description="ID of the candidate's resume")
    job_title: str = Field(..., description="Title of the position to recruit for")
    company_name: Optional[str] = Field(None, description="Name of the hiring company")
    job_requirements: Optional[Dict[str, Any]] = Field(
        None, 
        description="Job requirements including skills, experience, etc.",
        example={
            "skills": ["Python", "React", "AWS"],
            "min_years_experience": 5,
            "nice_to_have": ["Machine Learning", "DevOps"],
            "location": "Remote or San Francisco"
        }
    )
    custom_instructions: Optional[str] = Field(
        None,
        description="Additional instructions for message generation",
        example="Emphasize our startup culture and equity package"
    )


class OutreachMessageResponse(BaseModel):
    """Response schema for a single outreach message."""
    
    subject: str
    body: str
    quality_score: float = Field(..., ge=0, le=1)


class OutreachMessageGenerateResponse(BaseModel):
    """Response schema for message generation endpoint."""
    
    success: bool
    messages: Dict[str, OutreachMessageResponse] = Field(
        ...,
        description="Generated messages by style (casual, professional, technical)"
    )
    candidate_name: str
    candidate_title: str


class OutreachMessageDB(BaseModel):
    """Database schema for outreach messages."""
    
    id: UUID
    user_id: UUID
    resume_id: UUID
    subject: str
    body: str
    style: MessageStyle
    status: MessageStatus
    job_title: Optional[str]
    company_name: Optional[str]
    quality_score: Optional[float]
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]
    responded_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OutreachTemplateCreate(BaseModel):
    """Schema for creating an outreach template."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    subject_template: str = Field(..., max_length=500)
    body_template: str = Field(..., min_length=10)
    style: MessageStyle
    industry: Optional[str] = Field(None, max_length=100)
    role_level: Optional[str] = Field(None, max_length=50)
    job_function: Optional[str] = Field(None, max_length=100)
    is_public: bool = Field(False, description="Share template with community")


class OutreachTemplateResponse(BaseModel):
    """Response schema for outreach templates."""
    
    id: UUID
    name: str
    description: Optional[str]
    subject_template: str
    body_template: str
    style: MessageStyle
    industry: Optional[str]
    role_level: Optional[str]
    job_function: Optional[str]
    times_used: int
    avg_response_rate: Optional[float]
    is_public: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessagePerformanceTrack(BaseModel):
    """Schema for tracking message performance."""
    
    message_id: UUID
    event: str = Field(..., regex="^(sent|opened|responded|not_interested)$")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional event metadata",
        example={"response_time_hours": 24, "response_sentiment": "positive"}
    )


class OutreachAnalytics(BaseModel):
    """Analytics schema for outreach performance."""
    
    total_messages: int
    messages_sent: int
    messages_opened: int
    messages_responded: int
    overall_response_rate: float
    avg_response_time_hours: Optional[float]
    best_performing_style: Optional[MessageStyle]
    best_performing_time: Optional[str]  # e.g., "Tuesday 10am"
    
    by_style: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Performance breakdown by message style"
    )