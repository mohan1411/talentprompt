"""Import queue models for bulk LinkedIn imports."""

from typing import Dict, Any
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base


class ImportStatus(str, enum.Enum):
    """Import queue item status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportSource(str, enum.Enum):
    """Import source types."""
    MANUAL = "manual"
    EXTENSION = "extension"
    CSV_UPLOAD = "csv_upload"
    EXCEL_UPLOAD = "excel_upload"
    ZIP_ARCHIVE = "zip_archive"
    WEBHOOK = "webhook"


class ImportQueueItem(Base):
    """Queue item for bulk imports."""
    
    __tablename__ = "import_queue"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    profile_data = Column(JSON, nullable=False)  # LinkedIn profile data to import
    source = Column(Enum(ImportSource), default=ImportSource.MANUAL)
    status = Column(Enum(ImportStatus), default=ImportStatus.PENDING)
    priority = Column(Integer, default=0)  # Higher priority processed first
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Processing details
    attempts = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resume.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="import_queue_items")
    resume = relationship("Resume", back_populates="import_queue_item")


class ImportHistory(Base):
    """History of all imports for compliance tracking."""
    
    __tablename__ = "import_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resume.id"), nullable=True)
    source = Column(String, nullable=False)
    status = Column(String, nullable=False)
    imported_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional tracking
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="import_history")
    resume = relationship("Resume")


# Add relationships to existing models
from app.models.user import User
from app.models.resume import Resume

# Update User model
if not hasattr(User, 'import_queue_items'):
    User.import_queue_items = relationship("ImportQueueItem", back_populates="user")
if not hasattr(User, 'import_history'):
    User.import_history = relationship("ImportHistory", back_populates="user")

# Update Resume model
if not hasattr(Resume, 'import_queue_item'):
    Resume.import_queue_item = relationship("ImportQueueItem", back_populates="resume", uselist=False)