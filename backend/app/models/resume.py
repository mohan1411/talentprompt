"""Resume model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class Resume(Base):
    """Resume/Candidate model."""

    __tablename__ = "resumes"
    __table_args__ = (
        UniqueConstraint('user_id', 'linkedin_url', name='resumes_user_id_linkedin_url_key'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="resumes")
    
    # Basic Information
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, index=True)
    phone = Column(String)
    location = Column(String)
    
    # Professional Summary
    summary = Column(Text)
    current_title = Column(String)
    years_experience = Column(Integer)
    
    # Content
    raw_text = Column(Text)  # Original resume text
    parsed_data = Column(JSON)  # Structured data from parsing
    
    # Search & AI
    # Store embeddings as JSON array since Railway PostgreSQL doesn't have pgvector
    embedding = Column(JSON)  # Store embeddings as JSON array
    keywords = Column(JSON)  # Extracted keywords
    skills = Column(JSON)  # Extracted skills
    
    # Metadata
    original_filename = Column(String)
    file_size = Column(Integer)
    file_type = Column(String)
    job_position = Column(String, index=True)  # Job position/role this resume is for
    
    # LinkedIn Integration
    linkedin_url = Column(String, index=True)  # LinkedIn profile URL
    linkedin_data = Column(JSON)  # Raw LinkedIn data
    last_linkedin_sync = Column(DateTime(timezone=True), nullable=True)  # Last sync timestamp
    
    # Status
    status = Column(String, default="active")  # active, archived, deleted
    parse_status = Column(String, default="pending")  # pending, processing, completed, failed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    parsed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Analytics
    view_count = Column(Integer, default=0)
    search_appearance_count = Column(Integer, default=0)
    
    # AI Processing
    ai_analysis = Column(JSON)  # AI-generated insights
    match_scores = Column(JSON)  # Historical match scores
    
    # Relationships
    interview_sessions = relationship("InterviewSession", back_populates="resume")
    candidate_journeys = relationship("CandidateJourney", back_populates="resume")
    outreach_messages = relationship("OutreachMessage", back_populates="resume")