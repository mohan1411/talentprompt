"""Interview management endpoints."""

import logging
import re
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app import crud
from app.api import deps
from app.models.user import User
from app.models.resume import Resume
from app.models.interview import (
    InterviewSession, InterviewQuestion, InterviewFeedback,
    InterviewStatus, QuestionCategory
)
from app.schemas.interview import (
    InterviewPrepareRequest, InterviewPreparationResponse,
    InterviewSessionCreate, InterviewSessionUpdate, InterviewSessionResponse,
    GenerateQuestionsRequest, InterviewQuestionResponse,
    InterviewFeedbackCreate, QuestionResponseUpdate,
    InterviewAnalyticsResponse, InterviewScorecardResponse
)
from app.services.interview_ai import interview_ai_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/prepare", response_model=InterviewPreparationResponse)
async def prepare_interview(
    request: InterviewPrepareRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> InterviewPreparationResponse:
    """Prepare for an interview with AI-generated questions and insights."""
    
    # Get resume
    resume = await crud.resume.get(db, id=request.resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
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
        interview_type=request.interview_category  # Pass category to AI service
    )
    
    # Create interview session
    session = InterviewSession(
        resume_id=request.resume_id,
        interviewer_id=current_user.id,
        job_position=request.job_position,
        job_requirements=request.job_requirements,
        interview_type=request.interview_type,  # Mode: IN_PERSON, VIRTUAL, PHONE
        interview_category=request.interview_category,  # Category: general, technical, etc
        preparation_notes={
            "analysis": analysis,
            "company_culture": request.company_culture,
            "focus_areas": request.focus_areas
        },
        suggested_questions=questions_data["questions"]
    )
    
    db.add(session)
    await db.flush()
    
    # Create question records
    question_responses = []
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
        await db.flush()
        
        question_responses.append(InterviewQuestionResponse.model_validate(question))
    
    await db.commit()
    
    # Build response
    return InterviewPreparationResponse(
        session_id=session.id,
        candidate_summary=analysis["candidate_summary"],
        key_talking_points=analysis["key_talking_points"],
        areas_to_explore=analysis["areas_to_explore"],
        red_flags=analysis["red_flags"],
        suggested_questions=question_responses,
        interview_structure={
            "opening": "5 minutes - Introduction and rapport building",
            "main": f"{request.num_questions * 3} minutes - Core questions",
            "candidate_questions": "10 minutes - Candidate's questions",
            "closing": "5 minutes - Next steps and timeline"
        },
        estimated_duration=request.num_questions * 3 + 20  # 3 minutes per question + 20 minutes buffer
    )


@router.get("/sessions", response_model=List[InterviewSessionResponse])
async def get_interview_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[InterviewStatus] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[InterviewSessionResponse]:
    """Get interview sessions for current user."""
    
    query = select(InterviewSession).where(
        InterviewSession.interviewer_id == current_user.id
    )
    
    if status:
        query = query.where(InterviewSession.status == status)
    
    query = query.order_by(InterviewSession.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    # Convert to response models without questions for list view
    responses = []
    for session in sessions:
        response_dict = {
            "id": session.id,
            "resume_id": session.resume_id,
            "interviewer_id": session.interviewer_id,
            "job_position": session.job_position,
            "job_requirements": session.job_requirements,
            "interview_type": session.interview_type,
            "scheduled_at": session.scheduled_at,
            "duration_minutes": max(1, session.duration_minutes or 1),  # Ensure minimum 1 minute
            "status": session.status,
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "preparation_notes": session.preparation_notes,
            "suggested_questions": session.suggested_questions,
            "transcript": session.transcript,
            "notes": session.notes,
            "scorecard": session.scorecard,
            "overall_rating": session.overall_rating,
            "recommendation": session.recommendation,
            "strengths": session.strengths,
            "concerns": session.concerns,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "questions": []  # Don't load questions for list view
        }
        responses.append(InterviewSessionResponse(**response_dict))
    
    return responses


@router.get("/sessions/{session_id}", response_model=InterviewSessionResponse)
async def get_interview_session(
    session_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> InterviewSessionResponse:
    """Get a specific interview session."""
    
    query = select(InterviewSession).where(
        and_(
            InterviewSession.id == session_id,
            InterviewSession.interviewer_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Create response dict from session
    response_dict = {
        "id": session.id,
        "resume_id": session.resume_id,
        "interviewer_id": session.interviewer_id,
        "job_position": session.job_position,
        "job_requirements": session.job_requirements,
        "interview_type": session.interview_type,
        "interview_category": session.interview_category,
        "scheduled_at": session.scheduled_at,
        "duration_minutes": max(1, session.duration_minutes or 1),  # Ensure minimum 1 minute
        "status": session.status,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "preparation_notes": session.preparation_notes,
        "suggested_questions": session.suggested_questions,
        "transcript": session.transcript,
        "transcript_data": session.transcript_data,
        "notes": session.notes,
        "recordings": session.recordings,
        "scorecard": session.scorecard,
        "overall_rating": session.overall_rating,
        "recommendation": session.recommendation,
        "strengths": session.strengths,
        "concerns": session.concerns,
        "created_at": session.created_at,
        "updated_at": session.updated_at
    }
    
    # Load questions separately
    questions_query = select(InterviewQuestion).where(
        InterviewQuestion.session_id == session_id
    ).order_by(InterviewQuestion.order_index)
    
    questions_result = await db.execute(questions_query)
    questions = questions_result.scalars().all()
    
    response_dict["questions"] = [InterviewQuestionResponse.model_validate(q) for q in questions]
    
    return InterviewSessionResponse(**response_dict)


@router.patch("/sessions/{session_id}", response_model=InterviewSessionResponse)
async def update_interview_session(
    session_id: UUID,
    update_data: InterviewSessionUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> InterviewSessionResponse:
    """Update an interview session."""
    
    # Get session
    query = select(InterviewSession).where(
        and_(
            InterviewSession.id == session_id,
            InterviewSession.interviewer_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Handle status transitions
    if "status" in update_dict:
        if update_dict["status"] == InterviewStatus.IN_PROGRESS and not session.started_at:
            session.started_at = datetime.utcnow()
        elif update_dict["status"] == InterviewStatus.COMPLETED and not session.ended_at:
            session.ended_at = datetime.utcnow()
            # Calculate duration if we have both timestamps
            if session.started_at:
                # Ensure both timestamps are timezone-naive for comparison
                started = session.started_at.replace(tzinfo=None) if session.started_at.tzinfo else session.started_at
                ended = session.ended_at.replace(tzinfo=None) if session.ended_at.tzinfo else session.ended_at
                duration = (ended - started).total_seconds() / 60
                # Ensure minimum duration of 1 minute
                session.duration_minutes = max(1, int(duration))
    
    for field, value in update_dict.items():
        setattr(session, field, value)
    
    await db.commit()
    await db.refresh(session)
    
    # Create response dict from session
    response_dict = {
        "id": session.id,
        "resume_id": session.resume_id,
        "interviewer_id": session.interviewer_id,
        "job_position": session.job_position,
        "job_requirements": session.job_requirements,
        "interview_type": session.interview_type,
        "interview_category": session.interview_category,
        "scheduled_at": session.scheduled_at,
        "duration_minutes": max(1, session.duration_minutes or 1),  # Ensure minimum 1 minute
        "status": session.status,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "preparation_notes": session.preparation_notes,
        "suggested_questions": session.suggested_questions,
        "transcript": session.transcript,
        "transcript_data": session.transcript_data,
        "notes": session.notes,
        "recordings": session.recordings,
        "scorecard": session.scorecard,
        "overall_rating": session.overall_rating,
        "recommendation": session.recommendation,
        "strengths": session.strengths,
        "concerns": session.concerns,
        "created_at": session.created_at,
        "updated_at": session.updated_at
    }
    
    # Load questions for response
    questions_query = select(InterviewQuestion).where(
        InterviewQuestion.session_id == session_id
    ).order_by(InterviewQuestion.order_index)
    
    questions_result = await db.execute(questions_query)
    questions = questions_result.scalars().all()
    
    response_dict["questions"] = [InterviewQuestionResponse.model_validate(q) for q in questions]
    
    return InterviewSessionResponse(**response_dict)


@router.post("/sessions/{session_id}/questions", response_model=List[InterviewQuestionResponse])
async def generate_more_questions(
    session_id: UUID,
    request: GenerateQuestionsRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[InterviewQuestionResponse]:
    """Generate additional questions for an interview session."""
    
    # Get session
    session = await get_interview_session(session_id, db, current_user)
    
    # Get resume
    resume = await crud.resume.get(db, id=session.resume_id)
    
    # Generate questions
    questions_data = await interview_ai_service.generate_interview_questions(
        resume=resume,
        job_position=session.job_position,
        job_requirements=session.job_requirements,
        difficulty_level=request.difficulty_level or 3,
        num_questions=request.num_questions,
        interview_type=request.category.value if request.category else "general"
    )
    
    # Create question records
    question_responses = []
    
    # Get current max order index
    max_order_query = select(func.max(InterviewQuestion.order_index)).where(
        InterviewQuestion.session_id == session_id
    )
    max_order_result = await db.execute(max_order_query)
    max_order = max_order_result.scalar() or 0
    
    for i, q_data in enumerate(questions_data["questions"]):
        question = InterviewQuestion(
            session_id=session_id,
            question_text=q_data["question_text"],
            category=q_data["category"],
            difficulty_level=q_data["difficulty_level"],
            ai_generated=True,
            generation_context=request.context,
            expected_answer_points=q_data.get("expected_answer_points", []),
            order_index=max_order + i + 1
        )
        db.add(question)
        await db.flush()
        
        question_responses.append(InterviewQuestionResponse.model_validate(question))
    
    await db.commit()
    
    return question_responses


@router.put("/questions/{question_id}/response", response_model=InterviewQuestionResponse)
async def update_question_response(
    question_id: UUID,
    update_data: QuestionResponseUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> InterviewQuestionResponse:
    """Update a question's response data."""
    
    # Get question and verify access
    query = select(InterviewQuestion).join(InterviewSession).where(
        and_(
            InterviewQuestion.id == question_id,
            InterviewSession.interviewer_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Update fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(question, field, value)
    
    if update_data.asked and not question.asked_at:
        question.asked_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(question)
    
    return InterviewQuestionResponse.model_validate(question)


@router.post("/sessions/{session_id}/feedback", response_model=Dict)
async def add_interview_feedback(
    session_id: UUID,
    feedback_data: InterviewFeedbackCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict:
    """Add feedback for an interview session."""
    
    # Verify session exists
    session_query = select(InterviewSession).where(InterviewSession.id == session_id)
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Create feedback
    feedback = InterviewFeedback(
        session_id=session_id,
        reviewer_id=current_user.id,
        **feedback_data.model_dump(exclude={"session_id"})
    )
    
    db.add(feedback)
    await db.commit()
    
    return {"message": "Feedback added successfully", "feedback_id": str(feedback.id)}


@router.get("/sessions/{session_id}/scorecard", response_model=InterviewScorecardResponse)
async def generate_interview_scorecard(
    session_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> InterviewScorecardResponse:
    """Generate a comprehensive scorecard for an interview session."""
    
    # Get session
    query = select(InterviewSession).where(
        and_(
            InterviewSession.id == session_id,
            InterviewSession.interviewer_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Get resume
    resume = await crud.resume.get(db, id=session.resume_id)
    
    # Get question responses
    questions_query = select(InterviewQuestion).where(
        and_(
            InterviewQuestion.session_id == session_id,
            InterviewQuestion.asked == True
        )
    )
    questions_result = await db.execute(questions_query)
    questions = questions_result.scalars().all()
    
    # Generate scorecard
    responses_data = [
        {
            "question_text": q.question_text,
            "response_summary": q.response_summary,
            "response_rating": q.response_rating,
            "category": q.category.value if hasattr(q.category, 'value') else str(q.category)
        }
        for q in questions
    ]
    
    logger.info(f"Generating scorecard for session {session_id} with {len(questions)} rated questions")
    
    scorecard_data = await interview_ai_service.generate_interview_scorecard(
        session_data={
            "job_position": session.job_position,
            "duration_minutes": session.duration_minutes
        },
        responses=responses_data
    )
    
    # Update session with scorecard
    session.scorecard = scorecard_data
    session.overall_rating = scorecard_data.get("overall_rating")
    session.recommendation = scorecard_data.get("recommendation")
    session.strengths = scorecard_data.get("strengths", [])
    session.concerns = scorecard_data.get("concerns", [])
    
    await db.commit()
    
    return InterviewScorecardResponse(
        session_id=session_id,
        candidate_name=f"{resume.first_name} {resume.last_name}",
        position=session.job_position,
        interview_date=session.created_at,
        overall_rating=scorecard_data.get("overall_rating", 0),
        recommendation=scorecard_data.get("recommendation", "maybe"),
        technical_skills=scorecard_data.get("technical_skills", {}),
        soft_skills=scorecard_data.get("soft_skills", {}),
        culture_fit=scorecard_data.get("culture_fit", 3.0),
        strengths=scorecard_data.get("strengths", []),
        concerns=scorecard_data.get("concerns", []),
        next_steps=scorecard_data.get("next_steps", []),
        interviewer_notes=session.notes or "",
        key_takeaways=session.key_talking_points if hasattr(session, 'key_talking_points') else [],
        percentile_rank=scorecard_data.get("percentile_rank"),
        similar_candidates=[]  # TODO: Implement similar candidate search
    )


@router.post("/sessions/{session_id}/schedule-next", response_model=InterviewPreparationResponse)
async def schedule_next_round(
    session_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> InterviewPreparationResponse:
    """Schedule a follow-up interview round based on previous session performance."""
    
    # Get previous session
    query = select(InterviewSession).where(
        and_(
            InterviewSession.id == session_id,
            InterviewSession.interviewer_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    previous_session = result.scalar_one_or_none()
    
    if not previous_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    if previous_session.status != InterviewStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Previous interview must be completed first")
    
    # Get resume
    resume = await crud.resume.get(db, id=previous_session.resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Get previous questions and responses
    questions_query = select(InterviewQuestion).where(
        and_(
            InterviewQuestion.session_id == session_id,
            InterviewQuestion.asked == True
        )
    )
    questions_result = await db.execute(questions_query)
    previous_questions = questions_result.scalars().all()
    
    # Prepare context for follow-up
    previous_performance = {
        "overall_rating": previous_session.overall_rating,
        "recommendation": previous_session.recommendation,
        "strengths": previous_session.strengths or [],
        "concerns": previous_session.concerns or [],
        "questions_asked": [
            {
                "question": q.question_text,
                "rating": q.response_rating,
                "category": q.category.value if hasattr(q.category, 'value') else str(q.category)
            }
            for q in previous_questions
        ]
    }
    
    # Determine next interview type
    next_interview_type = "final"  # Default to final round
    if previous_session.interview_type == "general":
        next_interview_type = "technical"
    elif previous_session.interview_type == "technical":
        next_interview_type = "behavioral"
    elif previous_session.interview_type == "behavioral":
        next_interview_type = "final"
    
    # Generate follow-up analysis and questions
    analysis = await interview_ai_service.analyze_candidate_for_followup(
        resume=resume,
        job_position=previous_session.job_position,
        job_requirements=previous_session.job_requirements,
        previous_performance=previous_performance
    )
    
    questions_data = await interview_ai_service.generate_followup_questions(
        resume=resume,
        job_position=previous_session.job_position,
        job_requirements=previous_session.job_requirements,
        previous_performance=previous_performance,
        interview_type=next_interview_type,
        focus_areas=previous_session.concerns or []
    )
    
    # Create new interview session
    new_session = InterviewSession(
        resume_id=previous_session.resume_id,
        interviewer_id=current_user.id,
        job_position=previous_session.job_position,
        job_requirements=previous_session.job_requirements,
        interview_type=next_interview_type,
        preparation_notes={
            "analysis": analysis,
            "previous_session_id": str(session_id),
            "previous_performance": previous_performance,
            "round_number": (previous_session.preparation_notes or {}).get("round_number", 1) + 1
        },
        suggested_questions=questions_data["questions"]
    )
    
    db.add(new_session)
    await db.flush()
    
    # Create question records
    question_responses = []
    for q_data in questions_data["questions"]:
        question = InterviewQuestion(
            session_id=new_session.id,
            question_text=q_data["question_text"],
            category=q_data["category"],
            difficulty_level=q_data["difficulty_level"],
            ai_generated=True,
            generation_context=f"Follow-up from session {session_id}",
            expected_answer_points=q_data.get("expected_answer_points", []),
            order_index=q_data.get("order_index", 0)
        )
        db.add(question)
        await db.flush()
        
        question_responses.append(InterviewQuestionResponse.model_validate(question))
    
    await db.commit()
    
    # Build response
    return InterviewPreparationResponse(
        session_id=new_session.id,
        candidate_summary=analysis["candidate_summary"],
        key_talking_points=analysis["key_talking_points"],
        areas_to_explore=analysis["areas_to_explore"],
        red_flags=analysis["red_flags"],
        suggested_questions=question_responses,
        interview_structure={
            "opening": "5 minutes - Recap and rapport building",
            "main": f"{len(question_responses) * 3} minutes - Follow-up questions",
            "candidate_questions": "10 minutes - Candidate's questions",
            "closing": "5 minutes - Next steps and timeline"
        },
        estimated_duration=len(question_responses) * 3 + 20
    )


@router.get("/analytics", response_model=InterviewAnalyticsResponse)
async def get_interview_analytics(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    time_range: Optional[str] = Query("30d", description="Time range: 7d, 30d, 90d, all")
) -> InterviewAnalyticsResponse:
    """Get interview analytics for the current user."""
    
    # Set up time filter
    time_filter = None
    if time_range != "all":
        days = {"7d": 7, "30d": 30, "90d": 90}.get(time_range, 30)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        time_filter = InterviewSession.created_at >= cutoff_date
    
    # Build base query with time filter
    base_query = select(InterviewSession).where(
        InterviewSession.interviewer_id == current_user.id
    )
    if time_filter is not None:
        base_query = base_query.where(time_filter)
    
    # Get total interviews
    total_query = select(func.count(InterviewSession.id)).where(
        InterviewSession.interviewer_id == current_user.id
    )
    if time_filter is not None:
        total_query = total_query.where(time_filter)
    total_result = await db.execute(total_query)
    total_interviews = total_result.scalar() or 0
    
    # Get completed interviews count
    completed_query = select(func.count(InterviewSession.id)).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewSession.status == InterviewStatus.COMPLETED
        )
    )
    if time_filter is not None:
        completed_query = completed_query.where(time_filter)
    completed_result = await db.execute(completed_query)
    completed_interviews = completed_result.scalar() or 0
    
    # Get average duration
    avg_duration_query = select(func.avg(InterviewSession.duration_minutes)).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewSession.status == InterviewStatus.COMPLETED
        )
    )
    if time_filter is not None:
        avg_duration_query = avg_duration_query.where(time_filter)
    avg_duration_result = await db.execute(avg_duration_query)
    avg_duration = float(avg_duration_result.scalar() or 45.0)
    
    # Get average rating
    avg_rating_query = select(func.avg(InterviewSession.overall_rating)).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewSession.overall_rating.isnot(None)
        )
    )
    if time_filter is not None:
        avg_rating_query = avg_rating_query.where(time_filter)
    avg_rating_result = await db.execute(avg_rating_query)
    avg_rating = float(avg_rating_result.scalar() or 3.0)
    
    # Calculate hire rate
    hire_count_query = select(func.count(InterviewSession.id)).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewSession.recommendation == "hire"
        )
    )
    if time_filter is not None:
        hire_count_query = hire_count_query.where(time_filter)
    hire_count_result = await db.execute(hire_count_query)
    hire_count = hire_count_result.scalar() or 0
    
    hire_rate = (hire_count / completed_interviews * 100) if completed_interviews > 0 else 0
    
    # Get common strengths from completed sessions
    strengths_query = select(InterviewSession.strengths).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewSession.strengths.isnot(None),
            InterviewSession.status == InterviewStatus.COMPLETED
        )
    )
    if time_filter is not None:
        strengths_query = strengths_query.where(time_filter)
    strengths_result = await db.execute(strengths_query)
    all_strengths = strengths_result.scalars().all()
    
    # Count strength occurrences
    strength_counts = {}
    for strengths_list in all_strengths:
        if strengths_list:
            for strength in strengths_list:
                strength_counts[strength] = strength_counts.get(strength, 0) + 1
    
    common_strengths = [
        {"strength": strength, "count": count}
        for strength, count in sorted(strength_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    # Get common concerns from completed sessions
    concerns_query = select(InterviewSession.concerns).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewSession.concerns.isnot(None),
            InterviewSession.status == InterviewStatus.COMPLETED
        )
    )
    if time_filter is not None:
        concerns_query = concerns_query.where(time_filter)
    concerns_result = await db.execute(concerns_query)
    all_concerns = concerns_result.scalars().all()
    
    # Count concern occurrences
    concern_counts = {}
    for concerns_list in all_concerns:
        if concerns_list:
            for concern in concerns_list:
                concern_counts[concern] = concern_counts.get(concern, 0) + 1
    
    common_concerns = [
        {"concern": concern, "count": count}
        for concern, count in sorted(concern_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    # Get question effectiveness (top rated questions)
    questions_query = select(
        InterviewQuestion.question_text,
        func.avg(InterviewQuestion.response_rating).label("avg_rating"),
        func.count(InterviewQuestion.id).label("times_asked")
    ).join(
        InterviewSession
    ).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewQuestion.asked == True,
            InterviewQuestion.response_rating.isnot(None)
        )
    ).group_by(
        InterviewQuestion.question_text
    ).order_by(
        func.avg(InterviewQuestion.response_rating).desc()
    ).limit(10)
    
    if time_filter is not None:
        questions_query = questions_query.where(time_filter)
    
    questions_result = await db.execute(questions_query)
    question_stats = questions_result.all()
    
    question_effectiveness = [
        {
            "question": q.question_text[:100] + "..." if len(q.question_text) > 100 else q.question_text,
            "avg_rating": float(q.avg_rating),
            "times_asked": q.times_asked
        }
        for q in question_stats
    ]
    
    # Calculate interviewer consistency (standard deviation of ratings)
    consistency_query = select(
        func.stddev(InterviewSession.overall_rating)
    ).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewSession.overall_rating.isnot(None)
        )
    )
    if time_filter is not None:
        consistency_query = consistency_query.where(time_filter)
    
    consistency_result = await db.execute(consistency_query)
    rating_stddev = consistency_result.scalar() or 0.0
    
    # Convert stddev to consistency score (lower stddev = higher consistency)
    # Normalize to 0-1 scale where 1 is perfect consistency
    consistency_score = max(0, 1 - (float(rating_stddev) / 2.5))  # Assuming 2.5 is max acceptable stddev
    
    return InterviewAnalyticsResponse(
        total_interviews=total_interviews,
        avg_duration=round(avg_duration, 1),
        avg_rating=round(avg_rating, 1),
        hire_rate=round(hire_rate, 1),
        common_strengths=common_strengths if common_strengths else [
            {"strength": "No data yet", "count": 0}
        ],
        common_concerns=common_concerns if common_concerns else [
            {"concern": "No data yet", "count": 0}
        ],
        question_effectiveness=question_effectiveness if question_effectiveness else [
            {"question": "No questions rated yet", "avg_rating": 0.0, "times_asked": 0}
        ],
        interviewer_consistency={"overall": round(consistency_score, 2)}
    )


@router.get("/analytics/extended")
async def get_extended_analytics(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    time_range: Optional[str] = Query("30d", description="Time range: 7d, 30d, 90d, all")
) -> Dict[str, Any]:
    """Get extended interview analytics including all data for intelligence dashboard."""
    
    # Get basic analytics first
    basic_analytics = await get_interview_analytics(db, current_user, time_range)
    
    # Set up time filter
    time_filter = None
    if time_range != "all":
        days = {"7d": 7, "30d": 30, "90d": 90}.get(time_range, 30)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        time_filter = InterviewSession.created_at >= cutoff_date
    
    # Get completed interviews count
    completed_query = select(func.count(InterviewSession.id)).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewSession.status == InterviewStatus.COMPLETED
        )
    )
    if time_filter is not None:
        completed_query = completed_query.where(time_filter)
    completed_result = await db.execute(completed_query)
    completed_interviews = completed_result.scalar() or 0
    
    # Get skill coverage from questions asked
    skill_coverage_query = select(
        InterviewQuestion.category,
        func.count(InterviewQuestion.id).label("count")
    ).join(
        InterviewSession
    ).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewQuestion.asked == True
        )
    ).group_by(InterviewQuestion.category)
    
    if time_filter is not None:
        skill_coverage_query = skill_coverage_query.where(time_filter)
    
    skill_coverage_result = await db.execute(skill_coverage_query)
    skill_coverage_raw = skill_coverage_result.all()
    
    # Calculate skill coverage percentages
    total_questions = sum(s.count for s in skill_coverage_raw)
    skill_coverage = {}
    
    # Map categories to display names
    category_mapping = {
        QuestionCategory.TECHNICAL: "Technical Skills",
        QuestionCategory.BEHAVIORAL: "Communication",
        QuestionCategory.SITUATIONAL: "Situational Awareness",
        QuestionCategory.PROBLEM_SOLVING: "Problem Solving",
        QuestionCategory.EXPERIENCE: "Leadership",
        QuestionCategory.CULTURE_FIT: "Culture Fit"
    }
    
    for category, count in skill_coverage_raw:
        display_name = category_mapping.get(category, str(category))
        if total_questions > 0:
            skill_coverage[display_name] = int((count / total_questions) * 100)
        else:
            skill_coverage[display_name] = 0
    
    # Ensure all categories are present
    for display_name in category_mapping.values():
        if display_name not in skill_coverage:
            skill_coverage[display_name] = 0
    
    # Get sentiment distribution based on ratings
    sentiment_query = select(
        InterviewSession.overall_rating
    ).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewSession.overall_rating.isnot(None),
            InterviewSession.status == InterviewStatus.COMPLETED
        )
    )
    if time_filter is not None:
        sentiment_query = sentiment_query.where(time_filter)
    
    sentiment_result = await db.execute(sentiment_query)
    ratings = sentiment_result.scalars().all()
    
    positive = sum(1 for r in ratings if r >= 4)
    neutral = sum(1 for r in ratings if 2.5 <= r < 4)
    negative = sum(1 for r in ratings if r < 2.5)
    total_rated = len(ratings)
    
    sentiment_distribution = {
        "positive": int((positive / total_rated * 100)) if total_rated > 0 else 0,
        "neutral": int((neutral / total_rated * 100)) if total_rated > 0 else 0,
        "negative": int((negative / total_rated * 100)) if total_rated > 0 else 0
    }
    
    # Get top candidates
    top_candidates_query = select(
        InterviewSession,
        Resume
    ).join(
        Resume, InterviewSession.resume_id == Resume.id
    ).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewSession.overall_rating.isnot(None),
            InterviewSession.status == InterviewStatus.COMPLETED
        )
    ).order_by(
        InterviewSession.overall_rating.desc()
    ).limit(5)
    
    if time_filter is not None:
        top_candidates_query = top_candidates_query.where(time_filter)
    
    top_candidates_result = await db.execute(top_candidates_query)
    top_candidates_raw = top_candidates_result.all()
    
    top_candidates = [
        {
            "candidate_name": f"{resume.first_name} {resume.last_name}",
            "position": session.job_position,
            "rating": float(session.overall_rating or 0),
            "interview_date": session.created_at.isoformat()
        }
        for session, resume in top_candidates_raw
    ]
    
    # Get interview trends (daily counts for the period)
    if time_range == "7d":
        trend_days = 7
    elif time_range == "30d":
        trend_days = 10  # Show 10 data points for 30 days
    elif time_range == "90d":
        trend_days = 12  # Show 12 data points for 90 days
    else:
        trend_days = 10
    
    interview_trends = []
    for i in range(trend_days - 1, -1, -1):
        day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        day_query = select(
            func.count(InterviewSession.id),
            func.avg(InterviewSession.overall_rating)
        ).where(
            and_(
                InterviewSession.interviewer_id == current_user.id,
                InterviewSession.created_at >= day_start,
                InterviewSession.created_at < day_end
            )
        )
        
        day_result = await db.execute(day_query)
        count, avg_rating = day_result.one()
        
        interview_trends.append({
            "date": day_start.isoformat(),
            "count": count or 0,
            "average_rating": float(avg_rating or 0)
        })
    
    # Calculate interviewer performance metrics
    total_questions_query = select(func.count(InterviewQuestion.id)).join(
        InterviewSession
    ).where(
        InterviewSession.interviewer_id == current_user.id
    )
    if time_filter is not None:
        total_questions_query = total_questions_query.where(time_filter)
    total_questions_result = await db.execute(total_questions_query)
    total_questions = total_questions_result.scalar() or 0
    
    asked_questions_query = select(func.count(InterviewQuestion.id)).join(
        InterviewSession
    ).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewQuestion.asked == True
        )
    )
    if time_filter is not None:
        asked_questions_query = asked_questions_query.where(time_filter)
    asked_questions_result = await db.execute(asked_questions_query)
    asked_questions = asked_questions_result.scalar() or 0
    
    questions_asked_ratio = (asked_questions / total_questions) if total_questions > 0 else 0
    
    # Calculate follow-up rate (simplified - based on whether sessions have follow-up questions)
    sessions_with_followup_query = select(func.count(InterviewQuestion.id)).join(
        InterviewSession
    ).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewQuestion.follow_up_questions.isnot(None)
        )
    )
    if time_filter is not None:
        sessions_with_followup_query = sessions_with_followup_query.where(time_filter)
    sessions_with_followup_result = await db.execute(sessions_with_followup_query)
    sessions_with_followup = sessions_with_followup_result.scalar() or 0
    
    follow_up_rate = (sessions_with_followup / asked_questions) if asked_questions > 0 else 0
    
    # Time management score (sessions completed within target duration)
    target_duration = 60  # Target 60 minutes
    on_time_sessions_query = select(func.count(InterviewSession.id)).where(
        and_(
            InterviewSession.interviewer_id == current_user.id,
            InterviewSession.status == InterviewStatus.COMPLETED,
            InterviewSession.duration_minutes.between(target_duration * 0.8, target_duration * 1.2)
        )
    )
    if time_filter is not None:
        on_time_sessions_query = on_time_sessions_query.where(time_filter)
    on_time_sessions_result = await db.execute(on_time_sessions_query)
    on_time_sessions = on_time_sessions_result.scalar() or 0
    
    time_management_score = (on_time_sessions / completed_interviews) if completed_interviews > 0 else 0
    
    interviewer_performance = {
        "questions_asked_ratio": round(questions_asked_ratio, 2),
        "follow_up_rate": round(follow_up_rate, 2),
        "time_management_score": round(time_management_score, 2)
    }
    
    # Combine all analytics
    return {
        "total_interviews": basic_analytics.total_interviews,
        "completed_interviews": completed_interviews,
        "average_duration": basic_analytics.avg_duration,
        "average_rating": basic_analytics.avg_rating,
        "hire_rate": basic_analytics.hire_rate,
        "skill_coverage": skill_coverage,
        "sentiment_distribution": sentiment_distribution,
        "top_candidates": top_candidates,
        "common_strengths": [s["strength"] for s in basic_analytics.common_strengths],
        "common_concerns": [c["concern"] for c in basic_analytics.common_concerns],
        "interview_trends": interview_trends,
        "interviewer_performance": interviewer_performance,
        "question_effectiveness": basic_analytics.question_effectiveness,
        "interviewer_consistency": basic_analytics.interviewer_consistency
    }


@router.post("/sessions/{session_id}/upload-recording")
async def upload_interview_recording(
    session_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Upload an interview recording for transcription and analysis."""
    
    logger.info(f"Upload recording request for session {session_id} by user {current_user.id}")
    logger.info(f"File details: name={file.filename}, content_type={file.content_type}")
    
    # Get session
    query = select(InterviewSession).where(
        and_(
            InterviewSession.id == session_id,
            InterviewSession.interviewer_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Validate file type
    allowed_extensions = ['mp3', 'mp4', 'wav', 'm4a', 'webm', 'ogg', 'mpeg']
    file_extension = file.filename.split('.')[-1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Save file temporarily and check size
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
        content = await file.read()
        
        # Check file size after reading (max 500MB)
        if len(content) > 500 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 500MB limit")
            
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Process the recording
        from app.services.transcription import transcription_service
        
        # Update session with processing status
        session.status = InterviewStatus.PROCESSING
        session.recordings = session.recordings or []
        session.recordings.append({
            "filename": file.filename,
            "uploaded_at": datetime.utcnow().isoformat(),
            "status": "processing"
        })
        
        await db.commit()
        
        # Process transcription in background (for now, doing it synchronously)
        try:
            transcript_data = await transcription_service.transcribe_with_speakers(tmp_file_path)
            
            # Update session with transcript
            session.transcript = transcript_data["transcript_text"]
            session.transcript_data = transcript_data  # Store full analysis
            session.status = InterviewStatus.COMPLETED
            
            # Update recording status
            if session.recordings:
                session.recordings[-1]["status"] = "completed"
                session.recordings[-1]["transcript_id"] = datetime.utcnow().isoformat()
            
            await db.commit()
            await db.refresh(session)
            
            logger.info(f"Session {session_id} updated with transcript")
            logger.info(f"Transcript length: {len(session.transcript) if session.transcript else 0}")
            
            # Automatically trigger analysis
            try:
                logger.info(f"Triggering automatic analysis for session {session_id}")
                
                analysis = await interview_ai_service.analyze_transcript_content(
                    transcript_data=transcript_data,
                    session_data={
                        "job_position": session.job_position,
                        "interview_type": session.interview_type,
                        "interview_category": session.interview_category,
                        "duration_minutes": session.duration_minutes
                    }
                )
                
                # Generate scorecard from analysis
                scorecard_data = await interview_ai_service.generate_interview_scorecard(
                    session_data={
                        "job_position": session.job_position,
                        "duration_minutes": session.duration_minutes or 30
                    },
                    responses=analysis["responses_for_scorecard"]
                )
                
                # Update session with analysis results
                session.scorecard = scorecard_data
                session.overall_rating = float(scorecard_data.get("overall_rating", 0))
                session.recommendation = scorecard_data.get("recommendation", "maybe")
                session.strengths = scorecard_data.get("strengths", [])
                session.concerns = scorecard_data.get("concerns", [])
                
                # Store detailed analysis
                if not session.preparation_notes:
                    session.preparation_notes = {}
                session.preparation_notes["transcript_analysis"] = analysis["qa_analysis"]
                session.preparation_notes["transcript_insights"] = analysis["transcript_insights"]
                
                await db.commit()
                await db.refresh(session)
                
                logger.info(f"Analysis completed for session {session_id}")
                
            except Exception as analysis_error:
                logger.error(f"Auto-analysis failed: {str(analysis_error)}")
                # Don't fail the upload if analysis fails
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
            return {
                "message": "Recording uploaded and processed successfully",
                "transcript": transcript_data,
                "status": "completed",
                "analysis_available": bool(session.scorecard)
            }
            
        except Exception as e:
            logger.error(f"Transcription processing failed: {str(e)}")
            # Update status to show error
            session.status = InterviewStatus.COMPLETED
            if session.recordings:
                session.recordings[-1]["status"] = "error"
                session.recordings[-1]["error"] = str(e)
            await db.commit()
            
            return {
                "message": "Recording uploaded but transcription failed",
                "error": str(e),
                "status": "error"
            }
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/analyze-transcript")
async def analyze_interview_transcript(
    session_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Analyze interview transcript and generate AI insights."""
    
    # Get session with transcript
    query = select(InterviewSession).where(
        and_(
            InterviewSession.id == session_id,
            InterviewSession.interviewer_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    if not session.transcript_data:
        raise HTTPException(status_code=400, detail="No transcript available for analysis")
    
    try:
        # Analyze transcript
        logger.info(f"Analyzing transcript for session {session_id}")
        
        analysis = await interview_ai_service.analyze_transcript_content(
            transcript_data=session.transcript_data,
            session_data={
                "job_position": session.job_position,
                "interview_type": session.interview_type,
                "interview_category": session.interview_category,
                "duration_minutes": session.duration_minutes
            }
        )
        
        # Generate scorecard from analysis
        scorecard_data = await interview_ai_service.generate_interview_scorecard(
            session_data={
                "job_position": session.job_position,
                "duration_minutes": session.duration_minutes or 30
            },
            responses=analysis["responses_for_scorecard"]
        )
        
        # Update session with analysis results
        session.scorecard = scorecard_data
        session.overall_rating = float(scorecard_data.get("overall_rating", 0))
        session.recommendation = scorecard_data.get("recommendation", "maybe")
        session.strengths = scorecard_data.get("strengths", [])
        session.concerns = scorecard_data.get("concerns", [])
        
        # Store detailed analysis
        if not session.preparation_notes:
            session.preparation_notes = {}
        session.preparation_notes["transcript_analysis"] = analysis["qa_analysis"]
        session.preparation_notes["transcript_insights"] = analysis["transcript_insights"]
        
        await db.commit()
        await db.refresh(session)
        
        return {
            "message": "Transcript analyzed successfully",
            "scorecard": scorecard_data,
            "qa_analysis": analysis["qa_analysis"],
            "insights": analysis["transcript_insights"]
        }
        
    except Exception as e:
        logger.error(f"Error analyzing transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/sessions/{session_id}/manual-transcript")
async def save_manual_transcript(
    session_id: UUID,
    request: Dict[str, str],
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Save manually entered transcript and trigger analysis."""
    
    # Get session
    query = select(InterviewSession).where(
        and_(
            InterviewSession.id == session_id,
            InterviewSession.interviewer_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Get transcript text from request
    transcript_text = request.get("transcript", "").strip()
    if not transcript_text:
        raise HTTPException(status_code=400, detail="No transcript provided")
    
    try:
        # Parse the manual transcript into speaker format
        utterances = []
        speakers = {"A": {"utterances": [], "likely_role": "interviewer"}, 
                   "B": {"utterances": [], "likely_role": "candidate_1"}}
        
        # Split by lines and parse speaker labels
        lines = transcript_text.split('\n')
        current_speaker = None
        current_text = []
        timestamp = 0
        
        # More flexible speaker detection patterns
        interviewer_patterns = [
            '[interviewer]:', 'interviewer:', 'interviewer ', 
            'q:', 'question:', 'q.', 'q ', 
            '1.', '1)', '1 -', '1:', 
            'hr:', 'manager:', 'recruiter:'
        ]
        candidate_patterns = [
            '[candidate]:', 'candidate:', 'candidate ', 
            'a:', 'answer:', 'a.', 'a ', 
            '2.', '2)', '2 -', '2:', 
            'applicant:', 'interviewee:'
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for speaker label with flexible matching
            line_lower = line.lower()
            is_interviewer = any(pattern in line_lower for pattern in interviewer_patterns)
            is_candidate = any(pattern in line_lower for pattern in candidate_patterns)
            
            # Also check for name patterns (Name: at start of line)
            name_pattern = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:', line)
            if name_pattern and not is_interviewer and not is_candidate:
                # Assume first named speaker is interviewer, second is candidate
                if current_speaker is None:
                    is_interviewer = True
                else:
                    is_candidate = True
            
            if is_interviewer or is_candidate:
                # Save previous utterance if any
                if current_speaker and current_text:
                    utterance = {
                        "text": ' '.join(current_text),
                        "start": timestamp,
                        "end": timestamp + 5000,  # Mock 5 second utterances
                        "confidence": 0.95,
                        "speaker": current_speaker,
                        "role": "interviewer" if current_speaker == "A" else "candidate"
                    }
                    utterances.append(utterance)
                    speakers[current_speaker]["utterances"].append(utterance)
                    timestamp += 5000
                
                # Set new speaker
                current_speaker = "A" if is_interviewer else "B"
                
                # Extract text after the speaker label
                # Find first colon and take everything after it
                colon_idx = line.find(':')
                if colon_idx != -1:
                    text_after_colon = line[colon_idx + 1:].strip()
                    current_text = [text_after_colon] if text_after_colon else []
                else:
                    current_text = []
                    
            else:
                # Continue current speaker's text
                if current_speaker:
                    current_text.append(line)
                else:
                    # No speaker identified yet, try to guess
                    # If line starts with uppercase and is a question, likely interviewer
                    if line.strip() and line[0].isupper() and '?' in line:
                        current_speaker = "A"
                        current_text = [line]
                    else:
                        # Default to candidate
                        current_speaker = "B"
                        current_text = [line]
        
        # Save final utterance
        if current_speaker and current_text:
            utterance = {
                "text": ' '.join(current_text),
                "start": timestamp,
                "end": timestamp + 5000,
                "confidence": 0.95,
                "speaker": current_speaker
            }
            utterances.append(utterance)
            speakers[current_speaker]["utterances"].append(utterance)
        
        # Create transcript data structure
        transcript_data = {
            "transcript_text": transcript_text,
            "speakers": speakers,
            "utterances": utterances,
            "duration": (timestamp + 5000) / 1000,  # Convert to seconds
            "confidence": 0.95
        }
        
        # Update session with transcript
        session.transcript = transcript_text
        session.transcript_data = transcript_data
        session.status = InterviewStatus.COMPLETED
        
        # Set a duration if not set
        if not session.duration_minutes:
            session.duration_minutes = int(transcript_data["duration"] / 60) or 1
        
        await db.commit()
        await db.refresh(session)
        
        # Trigger analysis
        logger.info(f"Triggering analysis for manual transcript in session {session_id}")
        
        analysis = await interview_ai_service.analyze_transcript_content(
            transcript_data=transcript_data,
            session_data={
                "job_position": session.job_position,
                "interview_type": session.interview_type,
                "interview_category": session.interview_category,
                "duration_minutes": session.duration_minutes,
                "is_manual_transcript": True
            }
        )
        
        # Generate scorecard
        responses = analysis["responses_for_scorecard"]
        logger.info(f"Generating scorecard with {len(responses)} responses")
        if not responses:
            logger.warning("No responses extracted from transcript analysis - scorecard will use defaults")
        
        scorecard_data = await interview_ai_service.generate_interview_scorecard(
            session_data={
                "job_position": session.job_position,
                "duration_minutes": session.duration_minutes,
                "is_manual_transcript": True
            },
            responses=responses
        )
        
        # Update session with analysis
        session.scorecard = scorecard_data
        session.overall_rating = float(scorecard_data.get("overall_rating", 0))
        session.recommendation = scorecard_data.get("recommendation", "maybe")
        session.strengths = scorecard_data.get("strengths", [])
        session.concerns = scorecard_data.get("concerns", [])
        
        if not session.preparation_notes:
            session.preparation_notes = {}
        session.preparation_notes["transcript_analysis"] = analysis["qa_analysis"]
        session.preparation_notes["transcript_insights"] = analysis["transcript_insights"]
        session.preparation_notes["manual_entry"] = True
        
        await db.commit()
        
        return {
            "message": "Manual transcript saved and analyzed successfully",
            "analysis_available": True
        }
        
    except Exception as e:
        logger.error(f"Error processing manual transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process transcript: {str(e)}")


@router.post("/validate-transcript")
async def validate_transcript_format(
    request: Dict[str, str],
    current_user: User = Depends(deps.get_current_active_user)
):
    """Validate transcript format and provide feedback."""
    
    transcript_text = request.get("transcript", "").strip()
    if not transcript_text:
        return {
            "valid": False,
            "issues": ["No transcript provided"],
            "suggestions": ["Enter or paste an interview transcript"]
        }
    
    lines = transcript_text.split('\n')
    non_empty_lines = [l.strip() for l in lines if l.strip()]
    
    # Check for basic issues
    issues = []
    suggestions = []
    
    # Check for speaker labels
    has_colon = any(':' in line for line in non_empty_lines)
    if not has_colon:
        issues.append("No speaker labels detected")
        suggestions.append("Add speaker labels like '[Interviewer]:' or 'Q:' before questions")
    
    # Check for minimum length
    if len(non_empty_lines) < 4:
        issues.append("Transcript is too short")
        suggestions.append("Add at least 2 question-answer pairs")
    
    # Check for alternating pattern
    speaker_pattern = []
    for line in non_empty_lines:
        if ':' in line:
            if any(p in line.lower() for p in ['interviewer', 'q:', 'question', '1.', 'hr:']):
                speaker_pattern.append('I')
            elif any(p in line.lower() for p in ['candidate', 'a:', 'answer', '2.']):
                speaker_pattern.append('C')
    
    # Check if pattern alternates
    if len(speaker_pattern) >= 2:
        alternates = all(
            speaker_pattern[i] != speaker_pattern[i+1] 
            for i in range(len(speaker_pattern)-1)
        )
        if not alternates:
            issues.append("Multiple consecutive questions or answers detected")
            suggestions.append("Ensure questions and answers alternate")
    
    # Count detected Q&A pairs
    qa_count = len(speaker_pattern) // 2
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "suggestions": suggestions,
        "stats": {
            "lines": len(non_empty_lines),
            "speaker_labels_found": has_colon,
            "estimated_qa_pairs": qa_count
        }
    }


@router.post("/test-transcript-analysis")
async def test_transcript_analysis(
    request: Dict[str, str],
    current_user: User = Depends(deps.get_current_active_user)
):
    """Test transcript analysis without saving to database."""
    
    transcript_text = request.get("transcript", "").strip()
    if not transcript_text:
        raise HTTPException(status_code=400, detail="No transcript provided")
    
    # Parse the transcript
    utterances = []
    interviewer_patterns = ['[interviewer]:', 'interviewer:', 'sarah:', 'q:']
    candidate_patterns = ['[candidate]:', 'candidate:', 'aditya:', 'a:']
    
    lines = transcript_text.split('\n')
    current_speaker = None
    current_text = []
    timestamp = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        line_lower = line.lower()
        is_interviewer = any(pattern in line_lower for pattern in interviewer_patterns)
        is_candidate = any(pattern in line_lower for pattern in candidate_patterns)
        
        if is_interviewer or is_candidate:
            if current_speaker and current_text:
                utterances.append({
                    "text": ' '.join(current_text),
                    "start": timestamp,
                    "end": timestamp + 5000,
                    "speaker": current_speaker,
                    "role": "interviewer" if current_speaker == "A" else "candidate"
                })
                timestamp += 5000
            
            current_speaker = "A" if is_interviewer else "B"
            colon_idx = line.find(':')
            if colon_idx != -1:
                current_text = [line[colon_idx + 1:].strip()]
            else:
                current_text = []
        else:
            if current_speaker:
                current_text.append(line)
    
    # Save final utterance
    if current_speaker and current_text:
        utterances.append({
            "text": ' '.join(current_text),
            "start": timestamp,
            "end": timestamp + 5000,
            "speaker": current_speaker,
            "role": "interviewer" if current_speaker == "A" else "candidate_1"
        })
    
    # Test the analysis
    transcript_data = {
        "transcript_text": transcript_text,
        "utterances": utterances,
        "duration": len(utterances) * 5
    }
    
    analysis = await interview_ai_service.analyze_transcript_content(
        transcript_data=transcript_data,
        session_data={
            "job_position": request.get("position", "Software Developer"),
            "interview_type": "general",
            "is_manual_transcript": True
        }
    )
    
    return {
        "utterances_count": len(utterances),
        "qa_pairs_extracted": len(analysis["qa_analysis"].get("qa_pairs", [])),
        "analysis": analysis["qa_analysis"],
        "would_generate_default": len(analysis["responses_for_scorecard"]) == 0
    }


@router.post("/sessions/{session_id}/refresh-rating")
async def refresh_interview_rating(
    session_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Refresh the overall rating from the scorecard data."""
    
    # Get session
    query = select(InterviewSession).where(
        and_(
            InterviewSession.id == session_id,
            InterviewSession.interviewer_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    if not session.scorecard:
        raise HTTPException(status_code=400, detail="No scorecard data available")
    
    try:
        # Update rating from scorecard
        if isinstance(session.scorecard, dict):
            new_rating = float(session.scorecard.get("overall_rating", 0))
            session.overall_rating = new_rating
            
            # Also update recommendation if available
            if "recommendation" in session.scorecard:
                session.recommendation = session.scorecard["recommendation"]
            
            await db.commit()
            
            return {
                "message": "Rating refreshed successfully",
                "overall_rating": new_rating,
                "recommendation": session.recommendation
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid scorecard format")
            
    except Exception as e:
        logger.error(f"Error refreshing rating: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh rating: {str(e)}")


@router.post("/sessions/{session_id}/reanalyze")
async def reanalyze_interview_session(
    session_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Re-analyze an existing interview session with updated AI logic."""
    
    # Get session
    query = select(InterviewSession).where(
        and_(
            InterviewSession.id == session_id,
            InterviewSession.interviewer_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    if not session.transcript_data:
        raise HTTPException(status_code=400, detail="No transcript data available for re-analysis")
    
    try:
        logger.info(f"Re-analyzing session {session_id} with updated logic")
        
        # Check if this was a manual transcript
        is_manual = session.preparation_notes.get("manual_entry", False) if session.preparation_notes else False
        
        # Re-analyze transcript
        analysis = await interview_ai_service.analyze_transcript_content(
            transcript_data=session.transcript_data,
            session_data={
                "job_position": session.job_position,
                "interview_type": session.interview_type,
                "interview_category": session.interview_category,
                "duration_minutes": session.duration_minutes,
                "is_manual_transcript": is_manual
            }
        )
        
        # Re-generate scorecard
        scorecard_data = await interview_ai_service.generate_interview_scorecard(
            session_data={
                "job_position": session.job_position,
                "duration_minutes": session.duration_minutes,
                "is_manual_transcript": is_manual
            },
            responses=analysis["responses_for_scorecard"]
        )
        
        # Update session
        session.scorecard = scorecard_data
        session.overall_rating = float(scorecard_data.get("overall_rating", 0))
        session.recommendation = scorecard_data.get("recommendation", "maybe")
        session.strengths = scorecard_data.get("strengths", [])
        session.concerns = scorecard_data.get("concerns", [])
        
        # Update analysis data
        if not session.preparation_notes:
            session.preparation_notes = {}
        session.preparation_notes["transcript_analysis"] = analysis["qa_analysis"]
        session.preparation_notes["transcript_insights"] = analysis["transcript_insights"]
        session.preparation_notes["reanalyzed_at"] = datetime.utcnow().isoformat()
        
        await db.commit()
        await db.refresh(session)
        
        return {
            "message": "Session re-analyzed successfully",
            "overall_rating": session.overall_rating,
            "recommendation": session.recommendation,
            "mismatch_detected": scorecard_data.get("mismatch_detected", False)
        }
        
    except Exception as e:
        logger.error(f"Error re-analyzing session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to re-analyze: {str(e)}")