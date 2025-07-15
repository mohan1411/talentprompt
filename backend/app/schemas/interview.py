"""Interview-related Pydantic schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.interview import InterviewStatus, QuestionCategory


# Base schemas
class InterviewQuestionBase(BaseModel):
    """Base schema for interview questions."""
    question_text: str
    category: QuestionCategory
    difficulty_level: int = Field(ge=1, le=5)
    expected_answer_points: Optional[List[str]] = None


class InterviewSessionBase(BaseModel):
    """Base schema for interview sessions."""
    resume_id: UUID
    job_position: str
    job_requirements: Optional[Dict[str, Any]] = None
    interview_type: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=60, ge=1, le=480)


# Request schemas
class InterviewPrepareRequest(BaseModel):
    """Request to prepare for an interview."""
    resume_id: UUID
    job_position: str
    job_requirements: Optional[Dict[str, Any]] = None
    company_culture: Optional[str] = None
    interview_type: str = "general"  # general, technical, behavioral, final
    focus_areas: Optional[List[str]] = None
    difficulty_level: int = Field(default=3, ge=1, le=5)
    num_questions: int = Field(default=10, ge=5, le=30)


class GenerateQuestionsRequest(BaseModel):
    """Request to generate interview questions."""
    session_id: UUID
    category: Optional[QuestionCategory] = None
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)
    context: Optional[str] = None


class InterviewSessionCreate(InterviewSessionBase):
    """Schema for creating an interview session."""
    pass


class InterviewSessionUpdate(BaseModel):
    """Schema for updating an interview session."""
    status: Optional[InterviewStatus] = None
    notes: Optional[str] = None
    transcript: Optional[str] = None
    scorecard: Optional[Dict[str, Any]] = None
    overall_rating: Optional[float] = Field(None, ge=1, le=5)
    recommendation: Optional[str] = None
    strengths: Optional[List[str]] = None
    concerns: Optional[List[str]] = None


class InterviewFeedbackCreate(BaseModel):
    """Schema for creating interview feedback."""
    session_id: UUID
    technical_rating: Optional[float] = Field(None, ge=1, le=5)
    communication_rating: Optional[float] = Field(None, ge=1, le=5)
    culture_fit_rating: Optional[float] = Field(None, ge=1, le=5)
    overall_rating: float = Field(ge=1, le=5)
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    notes: Optional[str] = None
    recommendation: str = Field(..., pattern="^(hire|no_hire|maybe)$")
    competency_ratings: Optional[Dict[str, float]] = None


class QuestionResponseUpdate(BaseModel):
    """Schema for updating a question response."""
    asked: Optional[bool] = None
    response_summary: Optional[str] = None
    response_rating: Optional[float] = Field(None, ge=1, le=5)
    follow_up_questions: Optional[List[str]] = None


# Response schemas
class InterviewQuestionResponse(InterviewQuestionBase):
    """Response schema for interview questions."""
    id: UUID
    ai_generated: bool = True
    generation_context: Optional[str] = None
    asked: bool = False
    asked_at: Optional[datetime] = None
    response_summary: Optional[str] = None
    response_rating: Optional[float] = None
    follow_up_questions: Optional[List[str]] = None
    order_index: Optional[int] = None
    
    class Config:
        from_attributes = True


class InterviewPreparationResponse(BaseModel):
    """Response for interview preparation."""
    session_id: UUID
    candidate_summary: Dict[str, Any]
    key_talking_points: List[str]
    areas_to_explore: List[str]
    red_flags: List[str]
    suggested_questions: List[InterviewQuestionResponse]
    interview_structure: Dict[str, Any]
    estimated_duration: int


class InterviewSessionResponse(InterviewSessionBase):
    """Response schema for interview sessions."""
    id: UUID
    interviewer_id: UUID
    status: InterviewStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    preparation_notes: Optional[Dict[str, Any]] = None
    suggested_questions: Optional[List[Dict[str, Any]]] = None
    transcript: Optional[str] = None
    notes: Optional[str] = None
    scorecard: Optional[Dict[str, Any]] = None
    overall_rating: Optional[float] = None
    recommendation: Optional[str] = None
    strengths: Optional[List[str]] = None
    concerns: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    # Include related data - make it optional and set via dict
    questions: Optional[List[InterviewQuestionResponse]] = None
    
    class Config:
        from_attributes = True


class InterviewAnalyticsResponse(BaseModel):
    """Response for interview analytics."""
    total_interviews: int
    avg_duration: float
    avg_rating: float
    hire_rate: float
    common_strengths: List[Dict[str, Any]]  # Changed to Any to support both string and int values
    common_concerns: List[Dict[str, Any]]   # Changed to Any to support both string and int values
    question_effectiveness: List[Dict[str, Any]]
    interviewer_consistency: Dict[str, float]


class InterviewScorecardResponse(BaseModel):
    """Response for interview scorecard."""
    session_id: UUID
    candidate_name: str
    position: str
    interview_date: datetime
    overall_rating: float
    recommendation: str
    
    # Detailed ratings
    technical_skills: Dict[str, float]
    soft_skills: Dict[str, float]
    culture_fit: float
    
    # Summary
    strengths: List[str]
    concerns: List[str]
    next_steps: List[str]
    
    # Interviewer notes
    interviewer_notes: str
    key_takeaways: List[str]
    
    # Comparison
    percentile_rank: Optional[float] = None  # Compared to other candidates
    similar_candidates: Optional[List[Dict[str, Any]]] = None