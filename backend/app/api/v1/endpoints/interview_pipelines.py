"""API endpoints for interview pipeline management."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.sql import func

from app import crud
from app.api import deps
from app.models.user import User
from app.models.interview_pipeline import InterviewPipeline, CandidateJourney
from app.models.interview import InterviewSession
from app.models.resume import Resume
from app.schemas.interview_pipeline import (
    InterviewPipelineCreate,
    InterviewPipelineUpdate,
    InterviewPipelineResponse,
    CandidateJourneyCreate,
    CandidateJourneyUpdate,
    CandidateJourneyResponse,
    CandidateProgressResponse,
    InterviewStageConfig
)

router = APIRouter()


@router.post("/pipelines", response_model=InterviewPipelineResponse)
async def create_interview_pipeline(
    pipeline_data: InterviewPipelineCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> InterviewPipelineResponse:
    """Create a new interview pipeline configuration."""
    
    # Validate stages
    stage_names = [stage.name for stage in pipeline_data.stages]
    if len(stage_names) != len(set(stage_names)):
        raise HTTPException(status_code=400, detail="Stage names must be unique")
    
    # Validate prerequisites
    for stage in pipeline_data.stages:
        for prereq in stage.prerequisites:
            if prereq not in stage_names:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid prerequisite '{prereq}' for stage '{stage.name}'"
                )
    
    # Create pipeline
    pipeline = InterviewPipeline(
        **pipeline_data.model_dump(),
        created_by=current_user.id
    )
    
    db.add(pipeline)
    await db.commit()
    await db.refresh(pipeline)
    
    return InterviewPipelineResponse.model_validate(pipeline)


@router.get("/pipelines", response_model=List[InterviewPipelineResponse])
async def list_interview_pipelines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    job_role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[InterviewPipelineResponse]:
    """List all interview pipelines."""
    
    query = select(InterviewPipeline)
    
    if job_role:
        query = query.where(InterviewPipeline.job_role == job_role)
    
    if is_active is not None:
        query = query.where(InterviewPipeline.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    pipelines = result.scalars().all()
    
    return [InterviewPipelineResponse.model_validate(p) for p in pipelines]


@router.get("/pipelines/{pipeline_id}", response_model=InterviewPipelineResponse)
async def get_interview_pipeline(
    pipeline_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> InterviewPipelineResponse:
    """Get a specific interview pipeline."""
    
    result = await db.execute(
        select(InterviewPipeline).where(InterviewPipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return InterviewPipelineResponse.model_validate(pipeline)


@router.put("/pipelines/{pipeline_id}", response_model=InterviewPipelineResponse)
async def update_interview_pipeline(
    pipeline_id: UUID,
    update_data: InterviewPipelineUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> InterviewPipelineResponse:
    """Update an interview pipeline (admin only)."""
    
    result = await db.execute(
        select(InterviewPipeline).where(InterviewPipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(pipeline, field, value)
    
    await db.commit()
    await db.refresh(pipeline)
    
    return InterviewPipelineResponse.model_validate(pipeline)


@router.post("/journeys", response_model=CandidateJourneyResponse)
async def start_candidate_journey(
    journey_data: CandidateJourneyCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> CandidateJourneyResponse:
    """Start a candidate's journey through an interview pipeline."""
    
    # Check if journey already exists
    existing = await db.execute(
        select(CandidateJourney).where(
            and_(
                CandidateJourney.resume_id == journey_data.resume_id,
                CandidateJourney.pipeline_id == journey_data.pipeline_id,
                CandidateJourney.status == "in_progress"
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail="Candidate already has an active journey for this pipeline"
        )
    
    # Get pipeline
    pipeline_result = await db.execute(
        select(InterviewPipeline).where(InterviewPipeline.id == journey_data.pipeline_id)
    )
    pipeline = pipeline_result.scalar_one_or_none()
    
    if not pipeline or not pipeline.is_active:
        raise HTTPException(status_code=404, detail="Active pipeline not found")
    
    # Create journey
    journey = CandidateJourney(
        **journey_data.model_dump(),
        current_stage=pipeline.stages[0]["name"] if pipeline.stages else None
    )
    
    db.add(journey)
    await db.commit()
    await db.refresh(journey)
    
    # Create response with additional data
    response = CandidateJourneyResponse.model_validate(journey)
    response.pipeline = InterviewPipelineResponse.model_validate(pipeline)
    response.progress_percentage = 0
    response.next_stage = InterviewStageConfig(**pipeline.stages[0]) if pipeline.stages else None
    response.can_proceed = True
    
    return response


@router.get("/journeys/candidate/{resume_id}", response_model=List[CandidateJourneyResponse])
async def get_candidate_journeys(
    resume_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[CandidateJourneyResponse]:
    """Get all journeys for a specific candidate."""
    
    result = await db.execute(
        select(CandidateJourney)
        .where(CandidateJourney.resume_id == resume_id)
        .order_by(CandidateJourney.started_at.desc())
    )
    journeys = result.scalars().all()
    
    responses = []
    for journey in journeys:
        # Get pipeline
        pipeline_result = await db.execute(
            select(InterviewPipeline).where(InterviewPipeline.id == journey.pipeline_id)
        )
        pipeline = pipeline_result.scalar_one_or_none()
        
        if pipeline:
            response = await _build_journey_response(journey, pipeline, db)
            responses.append(response)
    
    return responses


@router.post("/journeys/{journey_id}/complete-stage", response_model=CandidateJourneyResponse)
async def complete_journey_stage(
    journey_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> CandidateJourneyResponse:
    """Mark a stage as completed in the candidate's journey."""
    
    # Get journey
    journey_result = await db.execute(
        select(CandidateJourney).where(CandidateJourney.id == journey_id)
    )
    journey = journey_result.scalar_one_or_none()
    
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")
    
    if journey.status != "in_progress":
        raise HTTPException(status_code=400, detail="Journey is not in progress")
    
    # Get interview session
    session_result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    
    if not session or session.status != "completed":
        raise HTTPException(status_code=400, detail="Interview session not completed")
    
    # Get pipeline
    pipeline_result = await db.execute(
        select(InterviewPipeline).where(InterviewPipeline.id == journey.pipeline_id)
    )
    pipeline = pipeline_result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Update journey
    current_stage_name = journey.current_stage
    if current_stage_name:
        # Add to completed stages
        completed_stages = journey.completed_stages or []
        if current_stage_name not in completed_stages:
            completed_stages.append(current_stage_name)
            journey.completed_stages = completed_stages
        
        # Add stage result
        stage_results = journey.stage_results or {}
        stage_results[current_stage_name] = {
            "session_id": str(session.id),
            "score": session.overall_rating or 0,
            "recommendation": session.recommendation or "maybe",
            "completed_at": datetime.utcnow().isoformat()
        }
        journey.stage_results = stage_results
        
        # Find next stage
        current_stage_idx = next(
            (i for i, s in enumerate(pipeline.stages) if s["name"] == current_stage_name), 
            -1
        )
        
        if current_stage_idx >= 0 and current_stage_idx < len(pipeline.stages) - 1:
            # Move to next stage
            next_stage = pipeline.stages[current_stage_idx + 1]
            
            # Check prerequisites
            prereqs_met = all(
                prereq in completed_stages 
                for prereq in next_stage.get("prerequisites", [])
            )
            
            if prereqs_met:
                journey.current_stage = next_stage["name"]
            else:
                # Find next stage with met prerequisites
                for stage in pipeline.stages[current_stage_idx + 1:]:
                    if all(p in completed_stages for p in stage.get("prerequisites", [])):
                        journey.current_stage = stage["name"]
                        break
        else:
            # Completed all stages
            journey.status = "completed"
            journey.completed_at = func.now()
            
            # Calculate overall score
            if stage_results:
                scores = [r["score"] for r in stage_results.values() if r.get("score")]
                if scores:
                    journey.overall_score = sum(scores) / len(scores)
            
            # Determine final recommendation
            if journey.overall_score:
                if journey.overall_score >= pipeline.min_overall_score:
                    journey.final_recommendation = "hire"
                else:
                    journey.final_recommendation = "no_hire"
    
    await db.commit()
    await db.refresh(journey)
    
    return await _build_journey_response(journey, pipeline, db)


@router.get("/progress/dashboard", response_model=List[CandidateProgressResponse])
async def get_hiring_progress_dashboard(
    status: Optional[str] = None,
    pipeline_id: Optional[UUID] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[CandidateProgressResponse]:
    """Get hiring progress dashboard showing all candidates in pipelines."""
    
    query = select(CandidateJourney)
    
    if status:
        query = query.where(CandidateJourney.status == status)
    
    if pipeline_id:
        query = query.where(CandidateJourney.pipeline_id == pipeline_id)
    
    query = query.order_by(CandidateJourney.updated_at.desc())
    
    result = await db.execute(query)
    journeys = result.scalars().all()
    
    progress_list = []
    for journey in journeys:
        # Get resume
        resume_result = await db.execute(
            select(Resume).where(Resume.id == journey.resume_id)
        )
        resume = resume_result.scalar_one_or_none()
        
        # Get pipeline
        pipeline_result = await db.execute(
            select(InterviewPipeline).where(InterviewPipeline.id == journey.pipeline_id)
        )
        pipeline = pipeline_result.scalar_one_or_none()
        
        if resume and pipeline:
            completed_count = len(journey.completed_stages or [])
            total_count = len(pipeline.stages)
            
            progress = CandidateProgressResponse(
                journey_id=journey.id,
                candidate_name=f"{resume.first_name} {resume.last_name}",
                job_position=journey.job_position,
                pipeline_name=pipeline.name,
                current_stage=journey.current_stage or "Not started",
                progress_percentage=int((completed_count / total_count * 100) if total_count > 0 else 0),
                completed_stages=completed_count,
                total_stages=total_count,
                overall_score=journey.overall_score,
                status=journey.status,
                last_activity=journey.updated_at,
                next_action=_get_next_action(journey, pipeline)
            )
            progress_list.append(progress)
    
    return progress_list


async def _build_journey_response(
    journey: CandidateJourney, 
    pipeline: InterviewPipeline,
    db: AsyncSession
) -> CandidateJourneyResponse:
    """Build comprehensive journey response with progress data."""
    
    response = CandidateJourneyResponse.model_validate(journey)
    response.pipeline = InterviewPipelineResponse.model_validate(pipeline)
    
    # Calculate progress
    completed_count = len(journey.completed_stages or [])
    total_count = len(pipeline.stages)
    response.progress_percentage = int((completed_count / total_count * 100) if total_count > 0 else 0)
    
    # Find next stage
    if journey.current_stage and journey.status == "in_progress":
        current_stage_data = next(
            (s for s in pipeline.stages if s["name"] == journey.current_stage), 
            None
        )
        if current_stage_data:
            response.next_stage = InterviewStageConfig(**current_stage_data)
            
            # Check if can proceed (prerequisites met)
            prereqs = current_stage_data.get("prerequisites", [])
            response.can_proceed = all(
                prereq in (journey.completed_stages or []) 
                for prereq in prereqs
            )
    
    return response


def _get_next_action(journey: CandidateJourney, pipeline: InterviewPipeline) -> Optional[str]:
    """Determine the next action for a candidate journey."""
    
    if journey.status == "completed":
        return "Review final results and make decision"
    elif journey.status == "rejected":
        return "Send rejection notification"
    elif journey.status == "withdrawn":
        return "Archive candidate record"
    elif journey.current_stage:
        return f"Schedule {journey.current_stage}"
    else:
        return "Start interview process"