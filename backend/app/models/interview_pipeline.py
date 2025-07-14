"""Interview pipeline models for multi-stage interview processes."""

from typing import List, Optional
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import Column, String, Boolean, Integer, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class InterviewPipeline(Base):
    """Model for interview pipeline configurations."""
    __tablename__ = "interview_pipelines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    job_role = Column(String)  # e.g., "Software Engineer", "Product Manager"
    is_active = Column(Boolean, default=True)
    
    # Pipeline configuration
    stages = Column(JSON)  # List of stage configurations
    # Example stages format:
    # [
    #   {
    #     "order": 1,
    #     "name": "Phone Screen",
    #     "type": "general",
    #     "required": true,
    #     "min_score": 3.0,
    #     "prerequisites": []
    #   },
    #   {
    #     "order": 2,
    #     "name": "Technical Assessment",
    #     "type": "technical",
    #     "required": true,
    #     "min_score": 3.5,
    #     "prerequisites": ["Phone Screen"]
    #   }
    # ]
    
    # Scoring configuration
    scoring_weights = Column(JSON)  # Weights for different interview types
    min_overall_score = Column(Integer, default=3)  # Minimum overall score to pass
    
    # Auto-recommendation rules
    auto_reject_on_fail = Column(Boolean, default=False)
    auto_approve_on_pass = Column(Boolean, default=False)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(sa.DateTime, default=func.now())
    updated_at = Column(sa.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="created_pipelines")
    candidate_journeys = relationship("CandidateJourney", back_populates="pipeline")


class CandidateJourney(Base):
    """Track candidate progress through interview pipeline."""
    __tablename__ = "candidate_journeys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("interview_pipelines.id"), nullable=False)
    job_position = Column(String, nullable=False)
    
    # Journey status
    status = Column(String, default="in_progress")  # in_progress, completed, rejected, withdrawn
    current_stage = Column(String)  # Name of current stage
    
    # Progress tracking
    completed_stages = Column(JSON, default=list)  # List of completed stage names
    stage_results = Column(JSON, default=dict)  # Map of stage name to results
    # Example stage_results:
    # {
    #   "Phone Screen": {
    #     "session_id": "uuid",
    #     "score": 4.2,
    #     "recommendation": "hire",
    #     "completed_at": "2025-01-10T10:00:00"
    #   }
    # }
    
    # Overall assessment
    overall_score = Column(sa.Float)
    final_recommendation = Column(String)  # hire, no_hire, maybe
    rejection_reason = Column(String)
    
    # Timestamps
    started_at = Column(sa.DateTime, default=func.now())
    completed_at = Column(sa.DateTime)
    updated_at = Column(sa.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    resume = relationship("Resume", back_populates="candidate_journeys")
    pipeline = relationship("InterviewPipeline", back_populates="candidate_journeys")
    interview_sessions = relationship("InterviewSession", back_populates="journey")