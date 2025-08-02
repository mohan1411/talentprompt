"""Script to create a default pipeline in the database."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models import Pipeline, User
from datetime import datetime


async def create_default_pipeline():
    """Create a default pipeline if none exists."""
    async with async_session_maker() as db:
        try:
            # Check if a default pipeline already exists
            result = await db.execute(
                select(Pipeline).where(Pipeline.is_default == True)
            )
            existing_default = result.scalar_one_or_none()
            
            if existing_default:
                print(f"Default pipeline already exists: {existing_default.name}")
                return
            
            # Get a superuser to set as creator
            result = await db.execute(
                select(User).where(User.is_superuser == True).limit(1)
            )
            superuser = result.scalar_one_or_none()
            
            if not superuser:
                print("No superuser found. Please create a superuser first.")
                return
            
            # Create default pipeline
            default_pipeline = Pipeline(
                name="Default Hiring Pipeline",
                description="Standard hiring workflow for all positions",
                stages=[
                    {
                        "id": "applied",
                        "name": "Applied",
                        "order": 1,
                        "color": "#9ca3af",
                        "type": "initial",
                        "actions": ["review", "reject"]
                    },
                    {
                        "id": "screening",
                        "name": "Screening",
                        "order": 2,
                        "color": "#3b82f6",
                        "type": "review",
                        "actions": ["schedule_interview", "reject", "move_to_interview"]
                    },
                    {
                        "id": "interview",
                        "name": "Interview",
                        "order": 3,
                        "color": "#8b5cf6",
                        "type": "interview",
                        "actions": ["schedule_next", "reject", "move_to_offer"]
                    },
                    {
                        "id": "offer",
                        "name": "Offer",
                        "order": 4,
                        "color": "#f59e0b",
                        "type": "decision",
                        "actions": ["send_offer", "negotiate", "reject"]
                    },
                    {
                        "id": "hired",
                        "name": "Hired",
                        "order": 5,
                        "color": "#10b981",
                        "type": "final",
                        "actions": ["onboard"]
                    },
                    {
                        "id": "rejected",
                        "name": "Rejected",
                        "order": 6,
                        "color": "#ef4444",
                        "type": "final",
                        "actions": ["archive"]
                    },
                    {
                        "id": "withdrawn",
                        "name": "Withdrawn",
                        "order": 7,
                        "color": "#6b7280",
                        "type": "final",
                        "actions": ["archive"]
                    }
                ],
                team_id=None,  # Global pipeline
                is_default=True,
                is_active=True,
                created_by=superuser.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(default_pipeline)
            await db.commit()
            
            print(f"Created default pipeline: {default_pipeline.name}")
            print(f"Pipeline ID: {default_pipeline.id}")
            print(f"Stages: {len(default_pipeline.stages)}")
            
        except Exception as e:
            print(f"Error creating default pipeline: {e}")
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(create_default_pipeline())