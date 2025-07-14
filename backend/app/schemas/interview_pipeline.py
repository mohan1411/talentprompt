"""Schemas for interview pipeline management."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InterviewStageConfig(BaseModel):
    """Configuration for a single interview stage."""
    order: int = Field(..., ge=1, le=10)
    name: str
    type: str  # general, technical, behavioral, final
    required: bool = True
    min_score: float = Field(3.0, ge=1, le=5)
    prerequisites: List[str] = []
    description: Optional[str] = None


class InterviewPipelineBase(BaseModel):
    """Base schema for interview pipelines."""
    name: str
    description: Optional[str] = None
    job_role: Optional[str] = None
    is_active: bool = True
    stages: List[InterviewStageConfig]
    scoring_weights: Optional[Dict[str, float]] = None
    min_overall_score: float = Field(3.0, ge=1, le=5)
    auto_reject_on_fail: bool = False
    auto_approve_on_pass: bool = False


class InterviewPipelineCreate(InterviewPipelineBase):
    """Schema for creating interview pipeline."""
    pass


class InterviewPipelineUpdate(BaseModel):
    """Schema for updating interview pipeline."""
    name: Optional[str] = None
    description: Optional[str] = None
    job_role: Optional[str] = None
    is_active: Optional[bool] = None
    stages: Optional[List[InterviewStageConfig]] = None
    scoring_weights: Optional[Dict[str, float]] = None
    min_overall_score: Optional[float] = Field(None, ge=1, le=5)
    auto_reject_on_fail: Optional[bool] = None
    auto_approve_on_pass: Optional[bool] = None


class InterviewPipelineResponse(InterviewPipelineBase):
    """Response schema for interview pipeline."""
    id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StageResult(BaseModel):
    """Result of a completed interview stage."""
    session_id: UUID
    score: float
    recommendation: str
    completed_at: datetime
    notes: Optional[str] = None


class CandidateJourneyBase(BaseModel):
    """Base schema for candidate journey."""
    resume_id: UUID
    pipeline_id: UUID
    job_position: str


class CandidateJourneyCreate(CandidateJourneyBase):
    """Schema for creating candidate journey."""
    pass


class CandidateJourneyUpdate(BaseModel):
    """Schema for updating candidate journey."""
    status: Optional[str] = None
    current_stage: Optional[str] = None
    overall_score: Optional[float] = None
    final_recommendation: Optional[str] = None
    rejection_reason: Optional[str] = None


class CandidateJourneyResponse(CandidateJourneyBase):
    """Response schema for candidate journey."""
    id: UUID
    status: str
    current_stage: Optional[str]
    completed_stages: List[str]
    stage_results: Dict[str, StageResult]
    overall_score: Optional[float]
    final_recommendation: Optional[str]
    rejection_reason: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    updated_at: datetime
    
    # Include pipeline details
    pipeline: Optional[InterviewPipelineResponse] = None
    
    # Progress calculation
    progress_percentage: Optional[int] = None
    next_stage: Optional[InterviewStageConfig] = None
    can_proceed: bool = False
    
    class Config:
        from_attributes = True


class CandidateProgressResponse(BaseModel):
    """Response for candidate progress overview."""
    journey_id: UUID
    candidate_name: str
    job_position: str
    pipeline_name: str
    current_stage: str
    progress_percentage: int
    completed_stages: int
    total_stages: int
    overall_score: Optional[float]
    status: str
    last_activity: datetime
    next_action: Optional[str]