"""Job model."""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class Job(Base):
    """Job model matching the database schema."""
    
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Job details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    requirements = Column(ARRAY(Text))
    nice_to_have = Column(ARRAY(Text))
    
    # Organization
    department = Column(String(100))
    location = Column(String(255))
    employment_type = Column(String(50))
    salary_range = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    interview_sessions = relationship("InterviewSession", backref="job")