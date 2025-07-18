"""Outreach message models."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Float, JSON, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class MessageStyle(str, enum.Enum):
    """Message style options."""
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    TECHNICAL = "technical"


class MessageStatus(str, enum.Enum):
    """Message status tracking."""
    GENERATED = "generated"
    SENT = "sent"
    OPENED = "opened"
    RESPONDED = "responded"
    NOT_INTERESTED = "not_interested"


class OutreachMessage(Base):
    """Outreach message model."""
    
    __tablename__ = "outreach_messages"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    resume_id = Column(PostgresUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    
    # Message content
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    style = Column(Enum(MessageStyle), nullable=False)
    
    # Job context
    job_title = Column(String(255))
    job_requirements = Column(JSON)  # Store required skills, experience, etc.
    company_name = Column(String(255))
    
    # Tracking
    status = Column(Enum(MessageStatus), default=MessageStatus.GENERATED)
    sent_at = Column(DateTime)
    opened_at = Column(DateTime)
    responded_at = Column(DateTime)
    
    # Performance metrics
    quality_score = Column(Float)  # AI-generated quality score
    response_rate = Column(Float)  # Updated when response received
    
    # Metadata
    generation_prompt = Column(Text)  # Store the prompt used
    model_version = Column(String(50))  # Track which AI model was used
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="outreach_messages")
    resume = relationship("Resume", back_populates="outreach_messages")


class OutreachTemplate(Base):
    """Saved outreach templates."""
    
    __tablename__ = "outreach_templates"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Template content
    subject_template = Column(String(500))
    body_template = Column(Text, nullable=False)
    style = Column(Enum(MessageStyle), nullable=False)
    
    # Categorization
    industry = Column(String(100))
    role_level = Column(String(50))  # junior, mid, senior, executive
    job_function = Column(String(100))  # engineering, sales, marketing, etc.
    
    # Performance
    times_used = Column(Integer, default=0)
    avg_response_rate = Column(Float)
    
    # Metadata
    is_public = Column(Boolean, default=False)  # Share with community
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")