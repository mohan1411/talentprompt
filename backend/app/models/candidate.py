"""Candidate model."""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Float, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class Candidate(Base):
    """Candidate model matching the database schema."""
    
    __tablename__ = "candidates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Link to resume if imported from resume
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"))
    
    # Basic Information
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255))
    phone = Column(String(50))
    
    # Professional Information
    current_title = Column(String(255))
    current_company = Column(String(255))
    years_of_experience = Column(Float)
    
    # Skills and qualifications
    skills = Column(ARRAY(Text))
    education = Column(JSON)
    experience = Column(JSON)
    
    # Location
    location = Column(String(255))
    
    # Online profiles
    linkedin_url = Column(String(500))
    github_url = Column(String(500))
    portfolio_url = Column(String(500))
    
    # Availability and expectations
    availability = Column(String(100))
    salary_expectation = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    resume = relationship("Resume", backref="candidate")
    interview_sessions = relationship("InterviewSession", back_populates="candidate")