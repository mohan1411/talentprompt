"""Pipeline and workflow management models."""

from datetime import datetime
from typing import Optional, List
import enum

from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, String, Text, Boolean,
    UniqueConstraint, CheckConstraint, Enum, JSON, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class PipelineStageType(str, enum.Enum):
    """Standard pipeline stage types."""
    SOURCED = "sourced"
    SCREENING = "screening"
    PHONE_INTERVIEW = "phone_interview"
    TECHNICAL_INTERVIEW = "technical_interview"
    ONSITE_INTERVIEW = "onsite_interview"
    REFERENCE_CHECK = "reference_check"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class PipelineActivityType(str, enum.Enum):
    """Types of activities that can occur in the pipeline."""
    STAGE_CHANGED = "stage_changed"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    NOTE_ADDED = "note_added"
    EMAIL_SENT = "email_sent"
    EMAIL_RECEIVED = "email_received"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    EVALUATION_SUBMITTED = "evaluation_submitted"
    OFFER_EXTENDED = "offer_extended"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_REJECTED = "offer_rejected"
    CANDIDATE_WITHDRAWN = "candidate_withdrawn"
    REJECTED = "rejected"


class Pipeline(Base):
    """Pipeline template for managing candidate workflows."""
    
    __tablename__ = "pipelines"
    __table_args__ = (
        UniqueConstraint('team_id', 'is_default', name='unique_default_pipeline_per_team'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Stages configuration as JSON array
    # Format: [{"id": "sourced", "name": "Sourced", "order": 1, "color": "#94a3b8", "type": "sourced", "actions": []}]
    stages = Column(JSON, nullable=False, default=[])
    
    team_id = Column(UUID(as_uuid=True))
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    pipeline_states = relationship("CandidatePipelineState", back_populates="pipeline")
    automations = relationship("PipelineAutomation", back_populates="pipeline", cascade="all, delete-orphan")
    team_members = relationship("PipelineTeamMember", back_populates="pipeline", cascade="all, delete-orphan")


class CandidatePipelineState(Base):
    """Tracks a candidate's current position in a pipeline."""
    
    __tablename__ = "candidate_pipeline_states"
    __table_args__ = (
        UniqueConstraint('candidate_id', 'pipeline_id', 'is_active', name='unique_active_candidate_pipeline'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("pipelines.id"), nullable=False)
    
    current_stage_id = Column(String(50), nullable=False)
    current_stage_type = Column(Enum(PipelineStageType, name='pipeline_stage_type', values_callable=lambda x: [e.value for e in x]))
    
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_at = Column(DateTime)
    
    entered_stage_at = Column(DateTime, default=datetime.utcnow)
    time_in_stage_seconds = Column(Integer, default=0)
    
    rejection_reason = Column(Text)
    rejection_details = Column(JSON)
    withdrawal_reason = Column(Text)
    
    is_active = Column(Boolean, default=True)
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Resume", backref="pipeline_states")
    pipeline = relationship("Pipeline", back_populates="pipeline_states")
    assignee = relationship("User", foreign_keys=[assigned_to])
    activities = relationship("PipelineActivity", back_populates="pipeline_state", cascade="all, delete-orphan")
    notes = relationship("CandidateNote", back_populates="pipeline_state")
    evaluations = relationship("CandidateEvaluation", back_populates="pipeline_state")
    communications = relationship("CandidateCommunication", back_populates="pipeline_state")
    interview_sessions = relationship("InterviewSession", back_populates="pipeline_state")


class PipelineActivity(Base):
    """Activity log for all pipeline actions."""
    
    __tablename__ = "pipeline_activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    pipeline_state_id = Column(UUID(as_uuid=True), ForeignKey("candidate_pipeline_states.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    activity_type = Column(Enum(PipelineActivityType, name='pipeline_activity_type', values_callable=lambda x: [e.value for e in x]), nullable=False)
    from_stage_id = Column(String(50))
    to_stage_id = Column(String(50))
    
    details = Column(JSON, default={})
    activity_metadata = Column("metadata", JSON, default={})  # Map to 'metadata' column in DB
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Resume")
    pipeline_state = relationship("CandidatePipelineState", back_populates="activities")
    user = relationship("User")


class CandidateNote(Base):
    """Comments and notes on candidates."""
    
    __tablename__ = "candidate_notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    pipeline_state_id = Column(UUID(as_uuid=True), ForeignKey("candidate_pipeline_states.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    is_private = Column(Boolean, default=False)
    mentioned_users = Column(ARRAY(UUID(as_uuid=True)), default=[])
    attachments = Column(JSON, default=[])
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Resume")
    pipeline_state = relationship("CandidatePipelineState", back_populates="notes")
    user = relationship("User")


class CandidateEvaluation(Base):
    """Interview feedback and evaluations."""
    
    __tablename__ = "candidate_evaluations"
    __table_args__ = (
        UniqueConstraint('candidate_id', 'evaluator_id', 'stage_id', name='unique_evaluation_per_stage'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range'),
        CheckConstraint("recommendation IN ('strong_yes', 'yes', 'neutral', 'no', 'strong_no')", name='valid_recommendation'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    pipeline_state_id = Column(UUID(as_uuid=True), ForeignKey("candidate_pipeline_states.id", ondelete="CASCADE"))
    evaluator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"))
    
    stage_id = Column(String(50), nullable=False)
    rating = Column(Integer)
    strengths = Column(Text)
    concerns = Column(Text)
    
    technical_assessment = Column(JSON)
    cultural_fit_assessment = Column(JSON)
    
    recommendation = Column(String(50))
    would_work_with = Column(Boolean)
    evaluation_form = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Resume")
    pipeline_state = relationship("CandidatePipelineState", back_populates="evaluations")
    evaluator = relationship("User")
    interview = relationship("InterviewSession")


class CandidateCommunication(Base):
    """Email and communication tracking."""
    
    __tablename__ = "candidate_communications"
    __table_args__ = (
        CheckConstraint("direction IN ('inbound', 'outbound')", name='valid_direction'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    pipeline_state_id = Column(UUID(as_uuid=True), ForeignKey("candidate_pipeline_states.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    direction = Column(String(10), nullable=False)
    channel = Column(String(50), default='email')
    
    subject = Column(String(500))
    content = Column(Text)
    
    thread_id = Column(String(255))
    message_id = Column(String(255))
    in_reply_to = Column(String(255))
    
    attachments = Column(JSON, default=[])
    communication_metadata = Column("metadata", JSON, default={})  # Map to 'metadata' column in DB
    
    sent_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    replied_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Resume")
    pipeline_state = relationship("CandidatePipelineState", back_populates="communications")
    user = relationship("User")


class PipelineAutomation(Base):
    """Automation rules for pipeline workflows."""
    
    __tablename__ = "pipeline_automations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    trigger_type = Column(String(50), nullable=False)  # stage_enter, time_in_stage, evaluation_complete, etc.
    trigger_config = Column(JSON, nullable=False)
    
    action_type = Column(String(50), nullable=False)  # send_email, move_stage, assign_user, add_tag, etc.
    action_config = Column(JSON, nullable=False)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pipeline = relationship("Pipeline", back_populates="automations")


class PipelineTeamMember(Base):
    """Team assignments and permissions for pipelines."""
    
    __tablename__ = "pipeline_team_members"
    __table_args__ = (
        UniqueConstraint('pipeline_id', 'user_id', name='unique_pipeline_member'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    role = Column(String(50), default='member')  # owner, admin, member, viewer
    stage_permissions = Column(JSON, default={})
    
    can_move_candidates = Column(Boolean, default=True)
    can_evaluate = Column(Boolean, default=True)
    can_communicate = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pipeline = relationship("Pipeline", back_populates="team_members")
    user = relationship("User")