"""Interview-related database models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import Column, String, Integer, Float, Text, JSON, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base


class InterviewStatus(str, enum.Enum):
    """Interview session status."""
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    PROCESSING = "PROCESSING"  # Processing uploaded recording


class QuestionCategory(str, enum.Enum):
    """Question categories."""
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SITUATIONAL = "situational"
    CULTURE_FIT = "culture_fit"
    EXPERIENCE = "experience"
    PROBLEM_SOLVING = "problem_solving"


class InterviewMode(str, enum.Enum):
    """Interview mode - how the interview is conducted."""
    IN_PERSON = "IN_PERSON"
    VIRTUAL = "VIRTUAL"
    PHONE = "PHONE"


class InterviewSession(Base):
    """Interview session model."""
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    # Using resume_id until database migration is complete
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    # candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=True)  # Commented out until DB migration
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    interviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Session details
    job_position = Column(String, nullable=False)
    job_requirements = Column(JSON)  # Skills, experience needed
    interview_type = Column(String)  # IN_PERSON, VIRTUAL, PHONE
    interview_category = Column(String)  # general, technical, behavioral, final
    scheduled_at = Column(DateTime)
    duration_minutes = Column(Integer)
    
    # Status tracking
    status = Column(Enum(InterviewStatus), default=InterviewStatus.SCHEDULED)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    
    # AI-generated content
    preparation_notes = Column(JSON)  # Key points, areas to explore
    suggested_questions = Column(JSON)  # AI-generated questions
    
    # Interview data
    transcript = Column(Text)  # Live transcription
    transcript_data = Column(JSON)  # Full transcript analysis with speakers
    notes = Column(Text)  # Interviewer notes
    recordings = Column(JSON)  # Audio/video recording URLs
    
    # Evaluation
    scorecard = Column(JSON)  # Structured evaluation data
    overall_rating = Column(Float)  # 1-5 scale
    recommendation = Column(String)  # hire, no_hire, maybe
    strengths = Column(JSON)  # List of identified strengths
    concerns = Column(JSON)  # List of concerns/red flags
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Pipeline journey tracking
    journey_id = Column(UUID(as_uuid=True), ForeignKey("candidate_journeys.id"), nullable=True)
    
    # Recruitment pipeline tracking
    pipeline_state_id = Column(UUID(as_uuid=True), ForeignKey("candidate_pipeline_states.id"), nullable=True)
    
    # Relationships
    resume = relationship("Resume", backref="interview_sessions")
    # candidate = relationship("Candidate", backref="interview_sessions")  # Commented out until DB migration
    interviewer = relationship("User", back_populates="conducted_interviews")
    questions = relationship("InterviewQuestion", back_populates="session")
    feedback = relationship("InterviewFeedback", back_populates="session", uselist=False)
    journey = relationship("CandidateJourney", back_populates="interview_sessions")
    pipeline_state = relationship("CandidatePipelineState", back_populates="interview_sessions")


class InterviewQuestion(Base):
    """Individual interview questions and responses."""
    __tablename__ = "interview_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False)
    
    # Question details
    question_text = Column(Text, nullable=False)
    category = Column(Enum(QuestionCategory), nullable=False)
    difficulty_level = Column(Integer)  # 1-5 scale
    
    # AI metadata
    ai_generated = Column(Boolean, default=True)
    generation_context = Column(JSON)  # Why this question was suggested
    expected_answer_points = Column(JSON)  # Key points to look for
    
    # Response tracking
    asked = Column(Boolean, default=False)
    asked_at = Column(DateTime)
    response_summary = Column(Text)
    response_rating = Column(Float)  # 1-5 scale
    follow_up_questions = Column(JSON)  # Dynamic follow-ups based on response
    
    # Order and grouping
    order_index = Column(Integer)
    question_group = Column(String)  # For organizing related questions
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("InterviewSession", back_populates="questions")


class InterviewFeedback(Base):
    """Feedback from multiple interviewers."""
    __tablename__ = "interview_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Ratings
    technical_rating = Column(Float)  # 1-5 scale
    communication_rating = Column(Float)
    culture_fit_rating = Column(Float)
    overall_rating = Column(Float)
    
    # Detailed feedback
    strengths = Column(Text)
    weaknesses = Column(Text)
    notes = Column(Text)
    recommendation = Column(String)  # hire, no_hire, maybe
    
    # Competency ratings
    competency_ratings = Column(JSON)  # {competency: rating} mapping
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("InterviewSession", back_populates="feedback")
    reviewer = relationship("User", back_populates="interview_reviews")


class InterviewTemplate(Base):
    """Reusable interview templates."""
    __tablename__ = "interview_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Template configuration
    job_role = Column(String)
    required_skills = Column(JSON)
    experience_level = Column(String)  # junior, mid, senior, lead
    
    # Question banks
    question_categories = Column(JSON)  # {category: [questions]}
    evaluation_criteria = Column(JSON)  # What to assess
    
    # Customization
    duration_minutes = Column(Integer, default=60)
    interview_stages = Column(JSON)  # phone, technical, behavioral, etc.
    
    # Usage tracking
    times_used = Column(Integer, default=0)
    avg_success_rate = Column(Float)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="interview_templates")