"""User model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Profile
    company = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    # Settings
    timezone = Column(String, default="UTC")
    language = Column(String, default="en")
    
    # Relationships
    conducted_interviews = relationship("InterviewSession", back_populates="interviewer")
    interview_reviews = relationship("InterviewFeedback", back_populates="reviewer")
    interview_templates = relationship("InterviewTemplate", back_populates="creator")
    created_pipelines = relationship("InterviewPipeline", back_populates="creator")
    
    # Supabase integration (if using Supabase Auth)
    supabase_id = Column(String, unique=True, nullable=True)