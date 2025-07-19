"""Analytics event model."""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import Column, String, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class AnalyticsEvent(Base):
    """Analytics event tracking model."""
    
    __tablename__ = "analytics_events"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), index=True)
    
    # Relationships
    user = relationship("User", back_populates="analytics_events")


# Common event types
class EventType:
    """Analytics event type constants."""
    
    # Authentication
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    
    # Search
    SEARCH_PERFORMED = "search_performed"
    SEARCH_RESULT_CLICKED = "search_result_clicked"
    
    # Resume
    RESUME_UPLOADED = "resume_uploaded"
    RESUME_VIEWED = "resume_viewed"
    RESUME_DOWNLOADED = "resume_downloaded"
    
    # LinkedIn
    LINKEDIN_PROFILE_IMPORTED = "linkedin_profile_imported"
    LINKEDIN_BULK_IMPORT = "linkedin_bulk_import"
    
    # Outreach
    OUTREACH_MESSAGE_GENERATED = "outreach_message_generated"
    OUTREACH_MESSAGE_COPIED = "outreach_message_copied"
    
    # Interview
    INTERVIEW_STARTED = "interview_started"
    INTERVIEW_COMPLETED = "interview_completed"
    
    # API Performance
    API_REQUEST = "api_request"
    API_ERROR = "api_error"
    
    # Feature Usage
    FEATURE_USED = "feature_used"
    PAGE_VIEWED = "page_viewed"