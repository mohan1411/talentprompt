"""Resume schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ResumeBase(BaseModel):
    """Base resume schema."""
    
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    current_title: Optional[str] = None
    years_experience: Optional[int] = None
    job_position: Optional[str] = None


class ResumeCreate(ResumeBase):
    """Schema for creating resume from upload."""
    
    raw_text: str
    original_filename: str
    file_size: int
    file_type: str


class ResumeUpdate(BaseModel):
    """Schema for updating resume."""
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    current_title: Optional[str] = None
    years_experience: Optional[int] = None
    skills: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    job_position: Optional[str] = None


class ResumeInDBBase(ResumeBase):
    """Base schema for resume in database."""
    
    id: UUID | str
    user_id: UUID | str
    raw_text: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    status: str = "active"
    parse_status: str = "pending"
    created_at: datetime
    updated_at: Optional[datetime] = None
    parsed_at: Optional[datetime] = None
    view_count: int = 0
    search_appearance_count: int = 0
    job_position: Optional[str] = None
    linkedin_url: Optional[str] = None
    
    @field_validator('id', 'user_id', mode='before')
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat() if v else None
        }


class Resume(ResumeInDBBase):
    """Schema for resume response."""
    
    id: str
    user_id: str


class ResumeSearchResult(BaseModel):
    """Schema for resume search results."""
    
    id: str
    first_name: str
    last_name: str
    current_title: Optional[str] = None
    location: Optional[str] = None
    years_experience: Optional[int] = None
    skills: Optional[List[str]] = None
    score: float
    highlights: List[str] = Field(default_factory=list)
    summary_snippet: Optional[str] = None
    job_position: Optional[str] = None
    linkedin_url: Optional[str] = None


class ResumeStatisticsItem(BaseModel):
    """Schema for a single statistics item."""
    
    date: str  # Format depends on aggregation: YYYY-MM-DD, YYYY-WW, YYYY-MM, YYYY
    count: int


class ResumeStatistics(BaseModel):
    """Schema for resume upload statistics response."""
    
    aggregation: str  # daily, weekly, monthly, yearly
    data: List[ResumeStatisticsItem]
    total_count: int
    start_date: str
    end_date: str