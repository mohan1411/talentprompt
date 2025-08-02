"""Script to update existing pipeline to add rejected and withdrawn stages."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.session import async_session_maker
from app.models import Pipeline, CandidatePipelineState, InterviewSession, Resume
from app.models.pipeline import PipelineActivity, PipelineActivityType
from datetime import datetime


async def update_existing_pipeline():
    """Update existing pipeline to add rejected and withdrawn stages."""
    async with async_session_maker() as db:
        try:
            # Get the default pipeline
            result = await db.execute(
                select(Pipeline).where(Pipeline.is_default == True)
            )
            pipeline = result.scalar_one_or_none()
            
            if not pipeline:
                print("No default pipeline found!")
                return
            
            print(f"Found pipeline: {pipeline.name}")
            print(f"Current stages: {len(pipeline.stages)}")
            
            # Check if rejected/withdrawn already exist
            stage_ids = [stage['id'] for stage in pipeline.stages]
            
            if 'rejected' in stage_ids and 'withdrawn' in stage_ids:
                print("Rejected and withdrawn stages already exist!")
            else:
                # Add missing stages
                updated_stages = pipeline.stages.copy()
                
                if 'rejected' not in stage_ids:
                    updated_stages.append({
                        "id": "rejected",
                        "name": "Rejected",
                        "order": 6,
                        "color": "#ef4444",
                        "type": "final",
                        "actions": []
                    })
                    print("Added 'rejected' stage")
                
                if 'withdrawn' not in stage_ids:
                    updated_stages.append({
                        "id": "withdrawn",
                        "name": "Withdrawn",
                        "order": 7,
                        "color": "#6b7280",
                        "type": "final",
                        "actions": []
                    })
                    print("Added 'withdrawn' stage")
                
                # Update the pipeline
                pipeline.stages = updated_stages
                pipeline.updated_at = datetime.utcnow()
                
                await db.commit()
                print(f"Pipeline updated! Now has {len(updated_stages)} stages")
            
            # Check for candidates with low ratings not in rejected stage
            from sqlalchemy.orm import joinedload
            
            result = await db.execute(
                select(InterviewSession)
                .options(joinedload(InterviewSession.pipeline_state))
                .where(
                    InterviewSession.overall_rating <= 2.0,
                    InterviewSession.status == 'completed'
                )
            )
            sessions = result.scalars().all()
            
            moved_count = 0
            for session in sessions:
                if session.pipeline_state and session.pipeline_state.current_stage_id != 'rejected':
                    # Get candidate name
                    resume_result = await db.execute(
                        select(Resume).where(Resume.id == session.resume_id)
                    )
                    resume = resume_result.scalar_one_or_none()
                    
                    if resume:
                        print(f"Moving {resume.first_name} {resume.last_name} (rating: {session.overall_rating}) to rejected stage")
                    
                    # Update pipeline state
                    old_stage = session.pipeline_state.current_stage_id
                    session.pipeline_state.current_stage_id = 'rejected'
                    session.pipeline_state.entered_stage_at = datetime.utcnow()
                    session.pipeline_state.updated_at = datetime.utcnow()
                    
                    # Create activity record
                    activity = PipelineActivity(
                        candidate_id=session.resume_id,
                        pipeline_state_id=session.pipeline_state.id,
                        user_id=session.interviewer_id,  # Use interviewer as the user
                        activity_type=PipelineActivityType.STAGE_CHANGED,
                        from_stage_id=old_stage,
                        to_stage_id='rejected',
                        details={
                            "reason": f"Interview completed with low rating ({session.overall_rating}/5)",
                            "automatic": True,
                            "interview_id": str(session.id)
                        }
                    )
                    db.add(activity)
                    moved_count += 1
            
            if moved_count > 0:
                await db.commit()
                print(f"\nMoved {moved_count} candidate(s) to rejected stage")
            else:
                print("\nNo candidates to move to rejected stage")
            
            # Display final pipeline stages
            print("\nFinal pipeline stages:")
            for stage in pipeline.stages:
                print(f"  - {stage['id']}: {stage['name']} (color: {stage['color']})")
            
            # Show candidate distribution
            result = await db.execute(
                select(
                    CandidatePipelineState.current_stage_id,
                    Pipeline.stages
                )
                .join(Pipeline, Pipeline.id == CandidatePipelineState.pipeline_id)
                .where(Pipeline.id == pipeline.id)
            )
            
            stage_counts = {}
            for row in result:
                stage_id = row[0]
                if stage_id not in stage_counts:
                    stage_counts[stage_id] = 0
                stage_counts[stage_id] += 1
            
            print("\nCandidate distribution:")
            for stage in pipeline.stages:
                count = stage_counts.get(stage['id'], 0)
                print(f"  - {stage['name']}: {count} candidate(s)")
                
        except Exception as e:
            print(f"Error updating pipeline: {e}")
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(update_existing_pipeline())