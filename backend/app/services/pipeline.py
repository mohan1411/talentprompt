"""Pipeline service for managing candidate workflows."""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Pipeline, CandidatePipelineState, PipelineActivity,
    CandidateNote, CandidateEvaluation, CandidateCommunication,
    PipelineAutomation, PipelineTeamMember,
    PipelineStageType, PipelineActivityType,
    Candidate, User
)
from app.models.pipeline import PipelineActivityType
from app.services.analytics import analytics_service
from app.services.email_service_production import email_service
from app.core.redis import get_redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class PipelineService:
    """Service for managing candidate pipelines and workflows."""
    
    async def create_pipeline(
        self,
        db: AsyncSession,
        name: str,
        description: Optional[str],
        stages: List[Dict[str, Any]],
        created_by: UUID,
        is_default: bool = False
    ) -> Pipeline:
        """Create a new pipeline template.
        
        Args:
            db: Database session
            name: Pipeline name
            description: Pipeline description
            stages: List of stage configurations
            created_by: User ID who created the pipeline
            is_default: Whether this is the default pipeline
            
        Returns:
            Created Pipeline object
        """
        # If setting as default, unset any existing default
        if is_default:
            await db.execute(
                update(Pipeline).where(
                    Pipeline.is_default == True
                ).values(is_default=False)
            )
        
        pipeline = Pipeline(
            name=name,
            description=description,
            stages=stages,
            is_default=is_default,
            created_by=created_by
        )
        
        db.add(pipeline)
        await db.commit()
        await db.refresh(pipeline)
        
        logger.info(f"Created pipeline '{name}' with {len(stages)} stages")
        return pipeline
    
    async def get_default_pipeline(
        self,
        db: AsyncSession
    ) -> Optional[Pipeline]:
        """Get the default pipeline.
        
        Args:
            db: Database session
            
        Returns:
            Default Pipeline or None
        """
        # Get the default pipeline
        result = await db.execute(
            select(Pipeline).where(
                and_(
                    Pipeline.is_default == True,
                    Pipeline.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def add_candidate_to_pipeline(
        self,
        db: AsyncSession,
        candidate_id: UUID,
        pipeline_id: UUID,
        assigned_to: Optional[UUID] = None,
        stage_id: Optional[str] = None,
        user_id: UUID = None
    ) -> CandidatePipelineState:
        """Add a candidate to a pipeline.
        
        Args:
            db: Database session
            candidate_id: Candidate ID
            pipeline_id: Pipeline ID
            assigned_to: Optional user to assign to
            stage_id: Optional starting stage (defaults to first stage)
            user_id: User performing the action
            
        Returns:
            Created CandidatePipelineState
        """
        # Get the pipeline
        result = await db.execute(
            select(Pipeline).where(Pipeline.id == pipeline_id)
        )
        pipeline = result.scalar_one_or_none()
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        # Check if candidate already exists in this pipeline
        existing = await db.execute(
            select(CandidatePipelineState).where(
                and_(
                    CandidatePipelineState.candidate_id == candidate_id,
                    CandidatePipelineState.pipeline_id == pipeline_id
                )
            )
        )
        if existing.scalar_one_or_none():
            logger.warning(f"Candidate {candidate_id} already in pipeline {pipeline_id}")
            raise ValueError("Candidate already exists in this pipeline")
        
        # Get the starting stage
        if not stage_id and pipeline.stages:
            stage_id = pipeline.stages[0]["id"]
        
        # Create new pipeline state
        pipeline_state = CandidatePipelineState(
            candidate_id=candidate_id,
            pipeline_id=pipeline_id,
            current_stage=stage_id,
            assigned_to=assigned_to
        )
        
        db.add(pipeline_state)
        await db.flush()
        
        # Log the activity
        if user_id:
            activity = PipelineActivity(
                pipeline_state_id=pipeline_state.id,
                performed_by=user_id,
                activity_type=PipelineActivityType.moved,
                to_stage=stage_id,
                details={"action": "added_to_pipeline"}
            )
            db.add(activity)
        
        await db.commit()
        await db.refresh(pipeline_state)
        
        logger.info(f"Added candidate {candidate_id} to pipeline {pipeline_id} at stage {stage_id}")
        return pipeline_state
    
    async def move_candidate_stage(
        self,
        db: AsyncSession,
        pipeline_state_id: UUID,
        new_stage_id: str,
        user_id: UUID,
        reason: Optional[str] = None
    ) -> CandidatePipelineState:
        """Move a candidate to a different stage.
        
        Args:
            db: Database session
            pipeline_state_id: Pipeline state ID
            new_stage_id: New stage ID
            user_id: User performing the action
            reason: Optional reason for the move
            
        Returns:
            Updated CandidatePipelineState
        """
        logger.info(f"Moving candidate in pipeline state {pipeline_state_id} to stage {new_stage_id}")
        
        # Get the current state
        result = await db.execute(
            select(CandidatePipelineState)
            .options(selectinload(CandidatePipelineState.pipeline))
            .where(CandidatePipelineState.id == pipeline_state_id)
        )
        pipeline_state = result.scalar_one_or_none()
        if not pipeline_state:
            logger.error(f"Pipeline state {pipeline_state_id} not found")
            raise ValueError(f"Pipeline state {pipeline_state_id} not found")
        
        old_stage_id = pipeline_state.current_stage
        logger.info(f"Current stage: {old_stage_id}, moving to: {new_stage_id}")
        
        # Calculate time in previous stage
        # Handle both naive and aware datetimes
        now = datetime.utcnow()
        stage_entered = pipeline_state.stage_entered_at
        if hasattr(stage_entered, 'tzinfo') and stage_entered.tzinfo is not None:
            # If stage_entered_at is timezone-aware, make now aware too
            from datetime import timezone
            now = datetime.now(timezone.utc)
        time_in_stage = int((now - stage_entered).total_seconds())
        
        # Update to new stage
        pipeline_state.current_stage = new_stage_id
        pipeline_state.stage_entered_at = datetime.utcnow()  # Use naive datetime for database
        
        # Store rejection/withdrawal reason in metadata if provided
        if reason and (new_stage_id == "rejected" or new_stage_id == "withdrawn"):
            if not pipeline_state.meta_data:
                pipeline_state.meta_data = {}
            pipeline_state.meta_data[f"{new_stage_id}_reason"] = reason
        
        # Log the activity
        activity = PipelineActivity(
            pipeline_state_id=pipeline_state.id,
            performed_by=user_id,
            activity_type=PipelineActivityType.moved,
            from_stage=old_stage_id,
            to_stage=new_stage_id,
            details={
                "reason": reason,
                "time_in_previous_stage": time_in_stage
            }
        )
        db.add(activity)
        
        await db.commit()
        await db.refresh(pipeline_state)
        
        # Trigger automations
        await self._trigger_stage_automations(db, pipeline_state, new_stage_id)
        
        # Track analytics
        await analytics_service.track_event(
            db=db,
            event_type="pipeline_stage_changed",
            event_data={
                "pipeline_id": str(pipeline_state.pipeline_id),
                "from_stage": old_stage_id,
                "to_stage": new_stage_id,
                "time_in_stage": time_in_stage
            },
            user_id=user_id
        )
        
        logger.info(f"Moved candidate from {old_stage_id} to {new_stage_id}")
        return pipeline_state
    
    async def assign_candidate(
        self,
        db: AsyncSession,
        pipeline_state_id: UUID,
        assignee_id: Optional[UUID],
        user_id: UUID
    ) -> CandidatePipelineState:
        """Assign or unassign a candidate to/from a user.
        
        Args:
            db: Database session
            pipeline_state_id: Pipeline state ID
            assignee_id: User to assign to (None to unassign)
            user_id: User performing the action
            
        Returns:
            Updated CandidatePipelineState
        """
        result = await db.execute(
            select(CandidatePipelineState).where(
                CandidatePipelineState.id == pipeline_state_id
            )
        )
        pipeline_state = result.scalar_one_or_none()
        if not pipeline_state:
            raise ValueError(f"Pipeline state {pipeline_state_id} not found")
        
        old_assignee = pipeline_state.assigned_to
        pipeline_state.assigned_to = assignee_id
        
        # Log the activity
        activity = PipelineActivity(
            pipeline_state_id=pipeline_state.id,
            performed_by=user_id,
            activity_type=PipelineActivityType.assigned,
            details={
                "old_assignee": str(old_assignee) if old_assignee else None,
                "new_assignee": str(assignee_id) if assignee_id else None
            }
        )
        db.add(activity)
        
        await db.commit()
        await db.refresh(pipeline_state)
        
        # Send notification to assignee
        if assignee_id and assignee_id != user_id:
            await self._send_assignment_notification(db, pipeline_state, assignee_id)
        
        return pipeline_state
    
    async def add_note(
        self,
        db: AsyncSession,
        candidate_id: UUID,
        content: str,
        user_id: UUID,
        pipeline_state_id: Optional[UUID] = None,
        is_private: bool = False,
        mentioned_users: List[UUID] = None
    ) -> CandidateNote:
        """Add a note to a candidate.
        
        Args:
            db: Database session
            candidate_id: Candidate ID
            content: Note content
            user_id: User adding the note
            pipeline_state_id: Optional pipeline state ID
            is_private: Whether the note is private
            mentioned_users: List of mentioned user IDs
            
        Returns:
            Created CandidateNote
        """
        note = CandidateNote(
            pipeline_state_id=pipeline_state_id,
            created_by=user_id,
            note=content,
            is_private=is_private
        )
        
        db.add(note)
        
        # Log activity if part of a pipeline
        if pipeline_state_id:
            activity = PipelineActivity(
                pipeline_state_id=pipeline_state_id,
                performed_by=user_id,
                activity_type=PipelineActivityType.noted,
                details={
                    "note_id": str(note.id),
                    "is_private": is_private,
                    "mentioned_users": [str(uid) for uid in (mentioned_users or [])]
                }
            )
            db.add(activity)
        
        await db.commit()
        await db.refresh(note)
        
        # Send notifications to mentioned users
        if mentioned_users:
            await self._send_mention_notifications(db, note, mentioned_users)
        
        return note
    
    async def add_evaluation(
        self,
        db: AsyncSession,
        candidate_id: UUID,
        evaluator_id: UUID,
        stage_id: str,
        rating: Optional[int],
        recommendation: Optional[str],
        strengths: Optional[str],
        concerns: Optional[str],
        pipeline_state_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        **kwargs
    ) -> CandidateEvaluation:
        """Add an evaluation for a candidate.
        
        Args:
            db: Database session
            candidate_id: Candidate ID
            evaluator_id: User providing evaluation
            stage_id: Stage being evaluated
            rating: Rating (1-5)
            recommendation: Recommendation type
            strengths: Candidate strengths
            concerns: Candidate concerns
            pipeline_state_id: Optional pipeline state ID
            interview_id: Optional interview session ID
            **kwargs: Additional evaluation fields
            
        Returns:
            Created CandidateEvaluation
        """
        evaluation = CandidateEvaluation(
            pipeline_state_id=pipeline_state_id,
            evaluator_id=evaluator_id,
            interview_id=interview_id,
            stage_id=stage_id,
            rating=rating,
            recommendation=recommendation,
            strengths=strengths,
            concerns=concerns,
            **kwargs
        )
        
        db.add(evaluation)
        
        # Log activity if part of a pipeline
        if pipeline_state_id:
            activity = PipelineActivity(
                pipeline_state_id=pipeline_state_id,
                performed_by=evaluator_id,
                activity_type=PipelineActivityType.evaluated,
                details={
                    "evaluation_id": str(evaluation.id),
                    "stage_id": stage_id,
                    "rating": rating,
                    "recommendation": recommendation
                }
            )
            db.add(activity)
        
        await db.commit()
        await db.refresh(evaluation)
        
        # Check if all evaluations are complete for auto-progression
        await self._check_stage_completion(db, candidate_id, stage_id)
        
        return evaluation
    
    async def get_pipeline_candidates(
        self,
        db: AsyncSession,
        pipeline_id: UUID,
        stage_id: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get candidates in a pipeline with their current states.
        
        Args:
            db: Database session
            pipeline_id: Pipeline ID
            stage_id: Optional filter by stage
            assigned_to: Optional filter by assignee
            include_inactive: Include inactive candidates
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of candidate data with pipeline state
        """
        query = (
            select(CandidatePipelineState, Candidate, User)
            .join(Candidate, CandidatePipelineState.candidate_id == Candidate.id)
            .outerjoin(User, CandidatePipelineState.assigned_to == User.id)
            .where(CandidatePipelineState.pipeline_id == pipeline_id)
        )
        
        if stage_id:
            query = query.where(CandidatePipelineState.current_stage == stage_id)
        
        if assigned_to:
            query = query.where(CandidatePipelineState.assigned_to == assigned_to)
        
        query = query.order_by(CandidatePipelineState.stage_entered_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        rows = result.all()
        
        candidates = []
        for pipeline_state, candidate, assignee in rows:
            # Calculate time in current stage
            # Handle both naive and aware datetimes
            now = datetime.utcnow()
            stage_entered = pipeline_state.stage_entered_at
            if hasattr(stage_entered, 'tzinfo') and stage_entered.tzinfo is not None:
                # If stage_entered_at is timezone-aware, make now aware too
                from datetime import timezone
                now = datetime.now(timezone.utc)
            time_in_stage = int((now - stage_entered).total_seconds())
            
            candidates.append({
                "id": str(candidate.id),
                "resume_id": str(candidate.resume_id) if candidate.resume_id else None,
                "pipeline_state_id": str(pipeline_state.id),
                "first_name": candidate.first_name,
                "last_name": candidate.last_name,
                "email": candidate.email,
                "current_title": candidate.current_title,
                "current_stage": pipeline_state.current_stage,
                "time_in_stage": time_in_stage,
                "assigned_to": {
                    "id": str(assignee.id),
                    "name": assignee.full_name or assignee.email
                } if assignee else None,
                "tags": pipeline_state.tags,
                "entered_stage_at": pipeline_state.stage_entered_at.isoformat()
            })
        
        return candidates
    
    async def get_candidate_timeline(
        self,
        db: AsyncSession,
        candidate_id: UUID,
        pipeline_state_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get timeline of activities for a candidate.
        
        Args:
            db: Database session
            candidate_id: Candidate ID
            pipeline_state_id: Optional filter by pipeline state
            
        Returns:
            List of timeline events
        """
        # Get activities
        query = (
            select(PipelineActivity, User)
            .join(User, PipelineActivity.performed_by == User.id)
            .join(CandidatePipelineState, PipelineActivity.pipeline_state_id == CandidatePipelineState.id)
            .where(CandidatePipelineState.candidate_id == candidate_id)
        )
        
        if pipeline_state_id:
            query = query.where(PipelineActivity.pipeline_state_id == pipeline_state_id)
        
        query = query.order_by(PipelineActivity.created_at.desc())
        
        result = await db.execute(query)
        activities = result.all()
        
        timeline = []
        for activity, user in activities:
            timeline.append({
                "id": str(activity.id),
                "type": activity.activity_type.value,
                "user": {
                    "id": str(user.id),
                    "name": user.full_name or user.username
                },
                "from_stage": activity.from_stage,
                "to_stage": activity.to_stage,
                "details": activity.details,
                "created_at": activity.created_at.isoformat()
            })
        
        # Get notes
        notes_query = (
            select(CandidateNote, User)
            .join(User, CandidateNote.created_by == User.id)
            .join(CandidatePipelineState, CandidateNote.pipeline_state_id == CandidatePipelineState.id)
            .where(CandidatePipelineState.candidate_id == candidate_id)
        )
        
        if pipeline_state_id:
            notes_query = notes_query.where(CandidateNote.pipeline_state_id == pipeline_state_id)
        
        notes_result = await db.execute(notes_query)
        notes = notes_result.all()
        
        for note, user in notes:
            if not note.is_private:  # Only include public notes in timeline
                timeline.append({
                    "id": str(note.id),
                    "type": "note",
                    "user": {
                        "id": str(user.id),
                        "name": user.full_name or user.username
                    },
                    "content": note.note,
                    "created_at": note.created_at.isoformat()
                })
        
        # Sort by created_at
        timeline.sort(key=lambda x: x["created_at"], reverse=True)
        
        return timeline
    
    async def _trigger_stage_automations(
        self,
        db: AsyncSession,
        pipeline_state: CandidatePipelineState,
        stage_id: str
    ):
        """Trigger automations for a stage change."""
        # Get automations for this pipeline and stage
        result = await db.execute(
            select(PipelineAutomation).where(
                and_(
                    PipelineAutomation.pipeline_id == pipeline_state.pipeline_id,
                    PipelineAutomation.is_active == True,
                    PipelineAutomation.trigger_stage == stage_id  # Check stage directly
                )
            )
        )
        automations = result.scalars().all()
        
        for automation in automations:
            # Check additional conditions if any
            if automation.trigger_condition and not self._check_conditions(automation.trigger_condition, pipeline_state):
                continue
            await self._execute_automation(db, automation, pipeline_state)
    
    def _check_conditions(self, conditions: dict, pipeline_state: CandidatePipelineState) -> bool:
        """Check if automation conditions are met."""
        # Simple condition checking - can be expanded
        for key, value in conditions.items():
            if key == "assigned_to" and pipeline_state.assigned_to != value:
                return False
            elif key == "has_tag" and value not in pipeline_state.tags:
                return False
        return True
    
    async def _execute_automation(
        self,
        db: AsyncSession,
        automation: PipelineAutomation,
        pipeline_state: CandidatePipelineState
    ):
        """Execute a pipeline automation."""
        try:
            if automation.action_type == "send_email":
                # Send automated email
                pass  # Implement email sending
            elif automation.action_type == "assign_user":
                # Auto-assign to user
                user_id = automation.action_config.get("user_id")
                if user_id:
                    pipeline_state.assigned_to = UUID(user_id)
            elif automation.action_type == "add_tag":
                # Add tag
                tag = automation.action_config.get("tag")
                if tag and tag not in pipeline_state.tags:
                    pipeline_state.tags.append(tag)
            
            await db.commit()
            logger.info(f"Executed automation {automation.name}")
        except Exception as e:
            logger.error(f"Failed to execute automation {automation.name}: {e}")
    
    async def _send_assignment_notification(
        self,
        db: AsyncSession,
        pipeline_state: CandidatePipelineState,
        assignee_id: UUID
    ):
        """Send notification when candidate is assigned."""
        # Get assignee and candidate info
        assignee_result = await db.execute(
            select(User).where(User.id == assignee_id)
        )
        assignee = assignee_result.scalar_one_or_none()
        
        if assignee and assignee.email:
            # Send email notification
            try:
                await email_service.send_email(
                    to_email=assignee.email,
                    subject="New Candidate Assignment",
                    html_content=f"""
                    <p>Hi {assignee.full_name or assignee.username},</p>
                    <p>A new candidate has been assigned to you for review.</p>
                    <p><a href="{settings.FRONTEND_URL}/candidates/{pipeline_state.candidate_id}">View Candidate</a></p>
                    """,
                    text_content=f"Hi {assignee.full_name or assignee.username}, a new candidate has been assigned to you."
                )
            except Exception as e:
                logger.error(f"Failed to send assignment notification: {e}")
    
    async def _send_mention_notifications(
        self,
        db: AsyncSession,
        note: CandidateNote,
        mentioned_users: List[UUID]
    ):
        """Send notifications to mentioned users."""
        # Get mentioned users
        result = await db.execute(
            select(User).where(User.id.in_(mentioned_users))
        )
        users = result.scalars().all()
        
        for user in users:
            if user.email:
                try:
                    await email_service.send_email(
                        to_email=user.email,
                        subject="You were mentioned in a candidate note",
                        html_content=f"""
                        <p>Hi {user.full_name or user.username},</p>
                        <p>You were mentioned in a note about a candidate.</p>
                        <p><a href="{settings.FRONTEND_URL}/candidates/{note.candidate_id}">View Note</a></p>
                        """,
                        text_content=f"Hi {user.full_name or user.username}, you were mentioned in a candidate note."
                    )
                except Exception as e:
                    logger.error(f"Failed to send mention notification: {e}")
    
    async def _check_stage_completion(
        self,
        db: AsyncSession,
        candidate_id: UUID,
        stage_id: str
    ):
        """Check if all evaluations are complete for auto-progression."""
        # This would check if all required evaluations are done
        # and potentially auto-move to next stage
        pass


# Create singleton instance
pipeline_service = PipelineService()