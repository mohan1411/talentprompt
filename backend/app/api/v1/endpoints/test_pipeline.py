"""Test endpoint for pipeline integration"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import logging

from app.api import deps
from app.models import CandidatePipelineState, PipelineActivity, InterviewSession
from app.models.user import User
from app.models.pipeline import PipelineActivityType
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/test-pipeline-move/{candidate_id}")
async def test_pipeline_move(
    candidate_id: UUID,
    new_stage: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Test endpoint to manually move a candidate to a stage"""
    
    # Get the candidate's pipeline state
    result = await db.execute(
        select(CandidatePipelineState).where(
            CandidatePipelineState.candidate_id == candidate_id,
            CandidatePipelineState.is_active == True
        )
    )
    pipeline_state = result.scalar_one_or_none()
    
    if not pipeline_state:
        raise HTTPException(status_code=404, detail="Candidate not in any active pipeline")
    
    old_stage = pipeline_state.current_stage_id
    
    # Update the stage
    pipeline_state.current_stage_id = new_stage
    pipeline_state.entered_stage_at = datetime.utcnow()
    pipeline_state.updated_at = datetime.utcnow()
    
    # Log activity
    activity = PipelineActivity(
        candidate_id=candidate_id,
        pipeline_state_id=pipeline_state.id,
        user_id=current_user.id,
        activity_type=PipelineActivityType.STAGE_CHANGED,
        from_stage_id=old_stage,
        to_stage_id=new_stage,
        details={"reason": "Manual test move"}
    )
    db.add(activity)
    
    await db.commit()
    
    return {
        "success": True,
        "candidate_id": str(candidate_id),
        "old_stage": old_stage,
        "new_stage": new_stage,
        "pipeline_state_id": str(pipeline_state.id)
    }


@router.get("/check-pipeline-state/{candidate_id}")
async def check_pipeline_state(
    candidate_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Check a candidate's current pipeline state"""
    
    # Get pipeline state
    ps_result = await db.execute(
        select(CandidatePipelineState).where(
            CandidatePipelineState.candidate_id == candidate_id,
            CandidatePipelineState.is_active == True
        )
    )
    pipeline_state = ps_result.scalar_one_or_none()
    
    # Get interviews
    i_result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.resume_id == candidate_id
        ).order_by(InterviewSession.created_at.desc())
    )
    interviews = i_result.scalars().all()
    
    # Get recent activities
    a_result = await db.execute(
        select(PipelineActivity).where(
            PipelineActivity.candidate_id == candidate_id
        ).order_by(PipelineActivity.created_at.desc()).limit(5)
    )
    activities = a_result.scalars().all()
    
    return {
        "candidate_id": str(candidate_id),
        "pipeline_state": {
            "id": str(pipeline_state.id) if pipeline_state else None,
            "current_stage": pipeline_state.current_stage_id if pipeline_state else None,
            "entered_stage_at": pipeline_state.entered_stage_at.isoformat() if pipeline_state else None,
            "is_active": pipeline_state.is_active if pipeline_state else None
        },
        "interviews": [
            {
                "id": str(i.id),
                "status": i.status.value if i.status else None,
                "pipeline_state_id": str(i.pipeline_state_id) if i.pipeline_state_id else None,
                "created_at": i.created_at.isoformat()
            }
            for i in interviews
        ],
        "recent_activities": [
            {
                "type": a.activity_type.value if hasattr(a.activity_type, 'value') else str(a.activity_type),
                "from_stage": a.from_stage_id,
                "to_stage": a.to_stage_id,
                "created_at": a.created_at.isoformat()
            }
            for a in activities
        ]
    }