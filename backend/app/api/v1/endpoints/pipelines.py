"""Pipeline and workflow management endpoints."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app import models
from app.api import deps
from app.services.pipeline import pipeline_service


router = APIRouter()


# Request/Response schemas
class PipelineStageSchema(BaseModel):
    """Schema for pipeline stage configuration."""
    id: str
    name: str
    order: int
    color: str
    type: Optional[str] = None
    actions: Optional[List[str]] = []


class PipelineCreateRequest(BaseModel):
    """Request schema for creating a pipeline."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    stages: List[PipelineStageSchema]
    team_id: Optional[UUID] = None
    is_default: bool = False


class PipelineResponse(BaseModel):
    """Response schema for pipeline."""
    id: UUID
    name: str
    description: Optional[str]
    stages: List[Dict[str, Any]]
    team_id: Optional[UUID]
    is_default: bool
    is_active: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class AddCandidateRequest(BaseModel):
    """Request schema for adding candidate to pipeline."""
    candidate_id: UUID
    pipeline_id: UUID
    assigned_to: Optional[UUID] = None
    stage_id: Optional[str] = None


class MoveCandidateRequest(BaseModel):
    """Request schema for moving candidate to different stage."""
    new_stage_id: str
    reason: Optional[str] = None


class AssignCandidateRequest(BaseModel):
    """Request schema for assigning candidate."""
    assignee_id: Optional[UUID] = None


class AddNoteRequest(BaseModel):
    """Request schema for adding a note."""
    content: str = Field(..., min_length=1)
    is_private: bool = False
    mentioned_users: Optional[List[UUID]] = []


class AddEvaluationRequest(BaseModel):
    """Request schema for adding evaluation."""
    stage_id: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    recommendation: Optional[str] = Field(None, pattern="^(strong_yes|yes|neutral|no|strong_no)$")
    strengths: Optional[str] = None
    concerns: Optional[str] = None
    technical_assessment: Optional[Dict[str, Any]] = None
    cultural_fit_assessment: Optional[Dict[str, Any]] = None
    would_work_with: Optional[bool] = None
    interview_id: Optional[UUID] = None


class CandidateInPipelineResponse(BaseModel):
    """Response schema for candidate in pipeline."""
    id: UUID
    pipeline_state_id: UUID
    first_name: str
    last_name: str
    email: Optional[str]
    current_title: Optional[str]
    current_stage: str
    time_in_stage: int
    assigned_to: Optional[Dict[str, Any]]
    tags: List[str]
    entered_stage_at: datetime
    is_active: bool


# Pipeline CRUD endpoints
@router.post("/", response_model=PipelineResponse)
async def create_pipeline(
    *,
    db: AsyncSession = Depends(deps.get_db),
    pipeline_in: PipelineCreateRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Create a new pipeline template."""
    if not current_user.is_superuser and pipeline_in.team_id:
        # TODO: Check if user has permission to create pipeline for team
        pass
    
    pipeline = await pipeline_service.create_pipeline(
        db=db,
        name=pipeline_in.name,
        description=pipeline_in.description,
        stages=[stage.dict() for stage in pipeline_in.stages],
        created_by=current_user.id,
        team_id=pipeline_in.team_id,
        is_default=pipeline_in.is_default
    )
    
    return pipeline


@router.get("/", response_model=List[PipelineResponse])
async def get_pipelines(
    db: AsyncSession = Depends(deps.get_db),
    team_id: Optional[UUID] = Query(None),
    include_inactive: bool = Query(False),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Get all accessible pipelines."""
    query = select(models.Pipeline)
    
    # Filter by team if specified
    if team_id:
        query = query.where(models.Pipeline.team_id == team_id)
    else:
        # Get global pipelines (no team)
        query = query.where(models.Pipeline.team_id.is_(None))
    
    if not include_inactive:
        query = query.where(models.Pipeline.is_active == True)
    
    result = await db.execute(query)
    pipelines = result.scalars().all()
    
    return pipelines


@router.get("/default", response_model=Optional[PipelineResponse])
async def get_default_pipeline(
    db: AsyncSession = Depends(deps.get_db),
    team_id: Optional[UUID] = Query(None),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Get the default pipeline for a team or global default."""
    pipeline = await pipeline_service.get_default_pipeline(
        db=db,
        team_id=team_id  # Remove reference to current_user.team_id
    )
    
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default pipeline found"
        )
    
    return pipeline


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    *,
    db: AsyncSession = Depends(deps.get_db),
    pipeline_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Get a specific pipeline."""
    result = await db.execute(
        select(models.Pipeline).where(models.Pipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )
    
    # TODO: Check if user has access to this pipeline
    
    return pipeline


@router.put("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    *,
    db: AsyncSession = Depends(deps.get_db),
    pipeline_id: UUID,
    pipeline_update: PipelineCreateRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Update a pipeline."""
    result = await db.execute(
        select(models.Pipeline).where(models.Pipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )
    
    # Check permissions
    if not current_user.is_superuser and pipeline.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this pipeline"
        )
    
    # Update pipeline
    pipeline.name = pipeline_update.name
    pipeline.description = pipeline_update.description
    pipeline.stages = [stage.dict() for stage in pipeline_update.stages]
    pipeline.is_default = pipeline_update.is_default
    pipeline.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(pipeline)
    
    return pipeline


@router.delete("/{pipeline_id}")
async def delete_pipeline(
    *,
    db: AsyncSession = Depends(deps.get_db),
    pipeline_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Delete (deactivate) a pipeline."""
    result = await db.execute(
        select(models.Pipeline).where(models.Pipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )
    
    # Check permissions
    if not current_user.is_superuser and pipeline.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this pipeline"
        )
    
    # Soft delete
    pipeline.is_active = False
    pipeline.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Pipeline deleted successfully"}


# Candidate pipeline management endpoints
@router.post("/candidates/add", response_model=Dict[str, Any])
async def add_candidate_to_pipeline(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: AddCandidateRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Add a candidate to a pipeline."""
    # Verify candidate exists and user has access
    result = await db.execute(
        select(models.Resume).where(
            and_(
                models.Resume.id == request.candidate_id,
                models.Resume.user_id == current_user.id
            )
        )
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found or access denied"
        )
    
    pipeline_state = await pipeline_service.add_candidate_to_pipeline(
        db=db,
        candidate_id=request.candidate_id,
        pipeline_id=request.pipeline_id,
        assigned_to=request.assigned_to,
        stage_id=request.stage_id,
        user_id=current_user.id
    )
    
    return {
        "pipeline_state_id": str(pipeline_state.id),
        "candidate_id": str(pipeline_state.candidate_id),
        "pipeline_id": str(pipeline_state.pipeline_id),
        "current_stage": pipeline_state.current_stage_id,
        "assigned_to": str(pipeline_state.assigned_to) if pipeline_state.assigned_to else None
    }


@router.put("/candidates/{pipeline_state_id}/move", response_model=Dict[str, Any])
async def move_candidate_stage(
    *,
    db: AsyncSession = Depends(deps.get_db),
    pipeline_state_id: UUID,
    request: MoveCandidateRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Move a candidate to a different stage."""
    pipeline_state = await pipeline_service.move_candidate_stage(
        db=db,
        pipeline_state_id=pipeline_state_id,
        new_stage_id=request.new_stage_id,
        user_id=current_user.id,
        reason=request.reason
    )
    
    return {
        "pipeline_state_id": str(pipeline_state.id),
        "current_stage": pipeline_state.current_stage_id,
        "entered_stage_at": pipeline_state.entered_stage_at.isoformat()
    }


@router.put("/candidates/{pipeline_state_id}/assign", response_model=Dict[str, Any])
async def assign_candidate(
    *,
    db: AsyncSession = Depends(deps.get_db),
    pipeline_state_id: UUID,
    request: AssignCandidateRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Assign or unassign a candidate."""
    pipeline_state = await pipeline_service.assign_candidate(
        db=db,
        pipeline_state_id=pipeline_state_id,
        assignee_id=request.assignee_id,
        user_id=current_user.id
    )
    
    return {
        "pipeline_state_id": str(pipeline_state.id),
        "assigned_to": str(pipeline_state.assigned_to) if pipeline_state.assigned_to else None,
        "assigned_at": pipeline_state.assigned_at.isoformat() if pipeline_state.assigned_at else None
    }


@router.get("/candidates/{pipeline_id}", response_model=List[CandidateInPipelineResponse])
async def get_pipeline_candidates(
    *,
    db: AsyncSession = Depends(deps.get_db),
    pipeline_id: UUID,
    stage_id: Optional[str] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    include_inactive: bool = Query(False),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Get candidates in a pipeline."""
    candidates = await pipeline_service.get_pipeline_candidates(
        db=db,
        pipeline_id=pipeline_id,
        stage_id=stage_id,
        assigned_to=assigned_to,
        include_inactive=include_inactive,
        limit=limit,
        offset=offset
    )
    
    return candidates


# Collaboration endpoints
@router.post("/candidates/{candidate_id}/notes", response_model=Dict[str, Any])
async def add_candidate_note(
    *,
    db: AsyncSession = Depends(deps.get_db),
    candidate_id: UUID,
    request: AddNoteRequest,
    pipeline_state_id: Optional[UUID] = Query(None),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Add a note to a candidate."""
    note = await pipeline_service.add_note(
        db=db,
        candidate_id=candidate_id,
        content=request.content,
        user_id=current_user.id,
        pipeline_state_id=pipeline_state_id,
        is_private=request.is_private,
        mentioned_users=request.mentioned_users
    )
    
    return {
        "note_id": str(note.id),
        "created_at": note.created_at.isoformat()
    }


@router.get("/candidates/{candidate_id}/notes", response_model=List[Dict[str, Any]])
async def get_candidate_notes(
    *,
    db: AsyncSession = Depends(deps.get_db),
    candidate_id: UUID,
    pipeline_state_id: Optional[UUID] = Query(None),
    include_private: bool = Query(False),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Get notes for a candidate."""
    query = select(models.CandidateNote, models.User).join(
        models.User, models.CandidateNote.user_id == models.User.id
    ).where(models.CandidateNote.candidate_id == candidate_id)
    
    if pipeline_state_id:
        query = query.where(models.CandidateNote.pipeline_state_id == pipeline_state_id)
    
    if not include_private:
        query = query.where(
            (models.CandidateNote.is_private == False) | 
            (models.CandidateNote.user_id == current_user.id)
        )
    
    query = query.order_by(models.CandidateNote.created_at.desc())
    
    result = await db.execute(query)
    notes = result.all()
    
    return [
        {
            "id": str(note.id),
            "content": note.content,
            "is_private": note.is_private,
            "user": {
                "id": str(user.id),
                "name": user.full_name or user.username
            },
            "mentioned_users": [str(uid) for uid in note.mentioned_users],
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat()
        }
        for note, user in notes
    ]


@router.post("/candidates/{candidate_id}/evaluations", response_model=Dict[str, Any])
async def add_candidate_evaluation(
    *,
    db: AsyncSession = Depends(deps.get_db),
    candidate_id: UUID,
    request: AddEvaluationRequest,
    pipeline_state_id: Optional[UUID] = Query(None),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Add an evaluation for a candidate."""
    evaluation = await pipeline_service.add_evaluation(
        db=db,
        candidate_id=candidate_id,
        evaluator_id=current_user.id,
        stage_id=request.stage_id,
        rating=request.rating,
        recommendation=request.recommendation,
        strengths=request.strengths,
        concerns=request.concerns,
        pipeline_state_id=pipeline_state_id,
        interview_id=request.interview_id,
        technical_assessment=request.technical_assessment,
        cultural_fit_assessment=request.cultural_fit_assessment,
        would_work_with=request.would_work_with
    )
    
    return {
        "evaluation_id": str(evaluation.id),
        "created_at": evaluation.created_at.isoformat()
    }


@router.get("/candidates/{candidate_id}/timeline", response_model=List[Dict[str, Any]])
async def get_candidate_timeline(
    *,
    db: AsyncSession = Depends(deps.get_db),
    candidate_id: UUID,
    pipeline_state_id: Optional[UUID] = Query(None),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Get timeline of activities for a candidate."""
    timeline = await pipeline_service.get_candidate_timeline(
        db=db,
        candidate_id=candidate_id,
        pipeline_state_id=pipeline_state_id
    )
    
    return timeline


# Analytics endpoints
@router.get("/{pipeline_id}/analytics", response_model=Dict[str, Any])
async def get_pipeline_analytics(
    *,
    db: AsyncSession = Depends(deps.get_db),
    pipeline_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Get analytics for a pipeline."""
    # Get stage distribution
    stage_query = select(
        models.CandidatePipelineState.current_stage_id,
        func.count(models.CandidatePipelineState.id).label("count")
    ).where(
        and_(
            models.CandidatePipelineState.pipeline_id == pipeline_id,
            models.CandidatePipelineState.is_active == True
        )
    ).group_by(models.CandidatePipelineState.current_stage_id)
    
    stage_result = await db.execute(stage_query)
    stage_distribution = {row[0]: row[1] for row in stage_result}
    
    # Get average time in stage
    time_query = select(
        models.CandidatePipelineState.current_stage_id,
        func.avg(models.CandidatePipelineState.time_in_stage_seconds).label("avg_time")
    ).where(
        and_(
            models.CandidatePipelineState.pipeline_id == pipeline_id,
            models.CandidatePipelineState.time_in_stage_seconds > 0
        )
    ).group_by(models.CandidatePipelineState.current_stage_id)
    
    time_result = await db.execute(time_query)
    avg_time_in_stage = {row[0]: float(row[1]) if row[1] else 0 for row in time_result}
    
    # Get conversion funnel
    # TODO: Calculate stage-to-stage conversion rates
    
    return {
        "stage_distribution": stage_distribution,
        "avg_time_in_stage": avg_time_in_stage,
        "total_candidates": sum(stage_distribution.values()),
        "active_candidates": sum(v for k, v in stage_distribution.items() if k not in ["hired", "rejected", "withdrawn"])
    }


class ScheduleInterviewRequest(BaseModel):
    """Request schema for scheduling an interview from pipeline."""
    job_position: str
    job_requirements: Optional[Dict[str, Any]] = None
    interview_type: Optional[str] = None  # IN_PERSON, VIRTUAL, PHONE
    interview_category: str = "general"  # general, technical, behavioral, final
    scheduled_at: Optional[datetime] = None
    duration_minutes: int = Field(default=60, ge=15, le=480)
    focus_areas: Optional[List[str]] = None
    difficulty_level: int = Field(default=3, ge=1, le=5)
    num_questions: int = Field(default=10, ge=5, le=30)


@router.post("/{pipeline_id}/candidates/{candidate_id}/interviews", response_model=Dict[str, Any])
async def schedule_interview_from_pipeline(
    *,
    db: AsyncSession = Depends(deps.get_db),
    pipeline_id: UUID,
    candidate_id: UUID,
    request: ScheduleInterviewRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """Schedule an interview for a candidate in a pipeline."""
    # Import here to avoid circular imports
    from app.schemas.interview import InterviewPrepareRequest
    from app.services.interview_ai import interview_ai_service
    
    # Verify candidate is in pipeline
    pipeline_state_query = select(models.CandidatePipelineState).where(
        and_(
            models.CandidatePipelineState.pipeline_id == pipeline_id,
            models.CandidatePipelineState.candidate_id == candidate_id,
            models.CandidatePipelineState.is_active == True
        )
    )
    
    result = await db.execute(pipeline_state_query)
    pipeline_state = result.scalar_one_or_none()
    
    if not pipeline_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found in pipeline"
        )
    
    # Get resume
    resume_result = await db.execute(
        select(models.Resume).where(models.Resume.id == candidate_id)
    )
    resume = resume_result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Analyze candidate
    analysis = await interview_ai_service.analyze_candidate_for_interview(
        resume=resume,
        job_position=request.job_position,
        job_requirements=request.job_requirements
    )
    
    # Generate questions
    questions_data = await interview_ai_service.generate_interview_questions(
        resume=resume,
        job_position=request.job_position,
        job_requirements=request.job_requirements,
        focus_areas=request.focus_areas,
        difficulty_level=request.difficulty_level,
        num_questions=request.num_questions,
        interview_type=request.interview_category
    )
    
    # Create interview session
    from app.models.interview import InterviewSession, InterviewQuestion
    
    session = InterviewSession(
        resume_id=candidate_id,
        interviewer_id=current_user.id,
        job_position=request.job_position,
        job_requirements=request.job_requirements,
        interview_type=request.interview_type,
        interview_category=request.interview_category,
        pipeline_state_id=pipeline_state.id,  # Link to pipeline
        scheduled_at=request.scheduled_at,
        duration_minutes=request.duration_minutes,
        preparation_notes={
            "analysis": analysis,
            "focus_areas": request.focus_areas,
            "pipeline_id": str(pipeline_id),
            "pipeline_state_id": str(pipeline_state.id),
            "current_stage": pipeline_state.current_stage_id
        },
        suggested_questions=questions_data["questions"]
    )
    
    db.add(session)
    await db.flush()
    
    # Create question records
    for q_data in questions_data["questions"]:
        question = InterviewQuestion(
            session_id=session.id,
            question_text=q_data["question_text"],
            category=q_data["category"],
            difficulty_level=q_data["difficulty_level"],
            ai_generated=True,
            generation_context=q_data.get("generation_context"),
            expected_answer_points=q_data.get("expected_answer_points", []),
            order_index=q_data.get("order_index", 0)
        )
        db.add(question)
    
    # Create pipeline activity
    activity = models.PipelineActivity(
        candidate_id=candidate_id,
        pipeline_state_id=pipeline_state.id,
        user_id=current_user.id,
        activity_type=models.PipelineActivityType.INTERVIEW_SCHEDULED,
        details={
            "interview_id": str(session.id),
            "job_position": request.job_position,
            "interview_type": request.interview_type,
            "interview_category": request.interview_category,
            "scheduled_at": request.scheduled_at.isoformat() if request.scheduled_at else None
        }
    )
    db.add(activity)
    
    # Auto-move candidate to Interview stage if not already there
    if pipeline_state.current_stage_id != "interview":
        updated_state = await pipeline_service.move_candidate_stage(
            db=db,
            pipeline_state_id=pipeline_state.id,
            new_stage_id="interview",
            user_id=current_user.id,
            reason="Interview scheduled - automatically moved to Interview stage"
        )
    
    await db.commit()
    
    return {
        "message": "Interview scheduled successfully",
        "interview_id": session.id,
        "pipeline_state_id": pipeline_state.id,
        "preparation_url": f"/interviews/{session.id}/prepare"
    }