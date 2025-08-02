"""Service to integrate interviews with pipeline workflow."""

import logging
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import InterviewSession, CandidatePipelineState, Pipeline
from app.services.pipeline import pipeline_service
from app.models.pipeline import PipelineActivityType

logger = logging.getLogger(__name__)


class InterviewPipelineIntegrationService:
    """Handles integration between interviews and pipeline stages."""
    
    async def handle_interview_completed(
        self,
        db: AsyncSession,
        interview: InterviewSession,
        user_id: UUID
    ) -> Optional[CandidatePipelineState]:
        """Handle pipeline updates when an interview is completed.
        
        Args:
            db: Database session
            interview: Completed interview session
            user_id: User who completed the interview
            
        Returns:
            Updated pipeline state if applicable
        """
        logger.info(f"Handling interview completion for interview {interview.id}")
        logger.info(f"Interview details - pipeline_state_id: {interview.pipeline_state_id}, recommendation: {interview.recommendation}, rating: {interview.overall_rating}")
        
        if not interview.pipeline_state_id:
            logger.info(f"Interview {interview.id} is not linked to a pipeline")
            return None
            
        # Get the pipeline state
        result = await db.execute(
            select(CandidatePipelineState)
            .where(CandidatePipelineState.id == interview.pipeline_state_id)
        )
        pipeline_state = result.scalar_one_or_none()
        
        if not pipeline_state:
            logger.warning(f"Pipeline state {interview.pipeline_state_id} not found")
            return None
            
        # Get the pipeline configuration
        result = await db.execute(
            select(Pipeline).where(Pipeline.id == pipeline_state.pipeline_id)
        )
        pipeline = result.scalar_one_or_none()
        
        if not pipeline:
            logger.warning(f"Pipeline {pipeline_state.pipeline_id} not found")
            return None
            
        # Determine next stage based on interview outcome
        logger.info(f"Current stage: {pipeline_state.current_stage_id}, Pipeline stages: {[s['id'] for s in pipeline.stages]}")
        
        next_stage = await self._determine_next_stage(
            current_stage=pipeline_state.current_stage_id,
            pipeline_stages=pipeline.stages,
            interview=interview
        )
        
        logger.info(f"Determined next stage: {next_stage}")
        
        if next_stage and next_stage != pipeline_state.current_stage_id:
            # Move candidate to next stage
            reason = self._generate_transition_reason(interview)
            
            updated_state = await pipeline_service.move_candidate_stage(
                db=db,
                pipeline_state_id=pipeline_state.id,
                new_stage_id=next_stage,
                user_id=user_id,
                reason=reason
            )
            
            logger.info(
                f"Moved candidate from {pipeline_state.current_stage_id} "
                f"to {next_stage} based on interview completion"
            )
            
            return updated_state
        else:
            logger.info(f"No stage transition needed. Current: {pipeline_state.current_stage_id}, Next: {next_stage}")
            
        return pipeline_state
    
    async def _determine_next_stage(
        self,
        current_stage: str,
        pipeline_stages: list,
        interview: InterviewSession
    ) -> Optional[str]:
        """Determine the next stage based on interview results.
        
        Logic:
        - If interview recommendation is "hire" or rating >= 4: Move to appropriate stage
        - If recommendation is "no_hire" or rating <= 2: Move to rejected
        - Otherwise: Stay in current stage for further review
        """
        # Find current stage in pipeline
        current_index = None
        for i, stage in enumerate(pipeline_stages):
            if stage["id"] == current_stage:
                current_index = i
                break
                
        if current_index is None:
            return None
            
        # Check interview outcome
        if interview.recommendation == "hire" or (interview.overall_rating and interview.overall_rating >= 4):
            # If already in interview stage or beyond, move to offer/hired
            if current_stage == "interview":
                # Look for "offer" stage
                for stage in pipeline_stages:
                    if stage["id"] == "offer":
                        return "offer"
                # If no offer stage, look for hired
                for stage in pipeline_stages:
                    if stage["id"] == "hired":
                        return "hired"
            elif current_stage in ["screening", "applied"]:
                # If in early stages, first move to interview (if not done yet)
                for stage in pipeline_stages:
                    if stage["id"] == "interview":
                        return "interview"
            
            # Otherwise, move to next stage if available
            if current_index < len(pipeline_stages) - 1:
                return pipeline_stages[current_index + 1]["id"]
                
        elif interview.recommendation == "no_hire" or (interview.overall_rating and interview.overall_rating <= 2):
            # Move to rejected
            return "rejected"
            
        # Default: stay in current stage
        return None
    
    def _generate_transition_reason(self, interview: InterviewSession) -> str:
        """Generate a reason for the stage transition based on interview results."""
        parts = []
        
        if interview.recommendation:
            parts.append(f"Interview recommendation: {interview.recommendation}")
            
        if interview.overall_rating:
            parts.append(f"Rating: {interview.overall_rating}/5")
            
        if interview.interview_category:
            parts.append(f"Interview type: {interview.interview_category}")
            
        return " | ".join(parts) if parts else "Based on interview completion"
    
    async def create_interview_from_pipeline(
        self,
        db: AsyncSession,
        pipeline_state_id: UUID,
        interview_data: Dict[str, Any],
        user_id: UUID
    ) -> InterviewSession:
        """Create an interview session linked to a pipeline state.
        
        Args:
            db: Database session
            pipeline_state_id: Pipeline state to link to
            interview_data: Interview creation data
            user_id: User creating the interview
            
        Returns:
            Created interview session
        """
        # Get pipeline state to extract candidate info
        result = await db.execute(
            select(CandidatePipelineState)
            .where(CandidatePipelineState.id == pipeline_state_id)
        )
        pipeline_state = result.scalar_one_or_none()
        
        if not pipeline_state:
            raise ValueError(f"Pipeline state {pipeline_state_id} not found")
            
        # Create interview with pipeline link
        interview_data["candidate_id"] = pipeline_state.candidate_id  # Use candidate_id not resume_id
        interview_data["pipeline_state_id"] = pipeline_state_id
        interview_data["interviewer_id"] = user_id
        
        interview = InterviewSession(**interview_data)
        db.add(interview)
        
        # Create pipeline activity
        from app.models.pipeline import PipelineActivity
        activity = PipelineActivity(
            candidate_id=pipeline_state.candidate_id,
            pipeline_state_id=pipeline_state_id,
            user_id=user_id,
            activity_type=PipelineActivityType.INTERVIEW_SCHEDULED,
            details={
                "interview_id": str(interview.id),
                "job_position": interview.job_position,
                "interview_type": interview.interview_type,
                "interview_category": interview.interview_category
            }
        )
        db.add(activity)
        
        # Auto-move candidate to Interview stage if not already there
        if pipeline_state.current_stage_id != "interview":
            from app.services.pipeline import pipeline_service
            await pipeline_service.move_candidate_stage(
                db=db,
                pipeline_state_id=pipeline_state_id,
                new_stage_id="interview",
                user_id=user_id,
                reason="Interview scheduled - automatically moved to Interview stage"
            )
        
        await db.flush()
        return interview


# Create singleton instance
interview_pipeline_service = InterviewPipelineIntegrationService()