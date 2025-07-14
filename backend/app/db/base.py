"""Database base configuration."""

# Import Base first
from app.db.base_class import Base

# Import all models to ensure they are registered with SQLAlchemy
from app.models.user import User  # noqa
from app.models.resume import Resume  # noqa
from app.models.interview import InterviewSession, InterviewQuestion, InterviewFeedback, InterviewTemplate  # noqa
from app.models.interview_pipeline import InterviewPipeline, CandidateJourney  # noqa