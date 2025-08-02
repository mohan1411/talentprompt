"""
Interview Flow Fix - Proper Stage Movement

The correct flow should be:
1. "Schedule Interview" - Creates interview session but DOESN'T move stage yet
2. "Start Interview" - Moves candidate to "Interview" stage
3. "Complete Interview" - Moves candidate to "Offer"/"Rejected" based on outcome
"""

# For prepare_interview endpoint - REMOVE the automatic stage movement
# Replace lines 111-180 with this simpler version:

    # Create pipeline activity if linked to pipeline
    if request.pipeline_state_id:
        logger.info(f"Creating interview scheduled activity for pipeline_state_id: {request.pipeline_state_id}")
        
        activity = PipelineActivity(
            candidate_id=request.resume_id,
            pipeline_state_id=request.pipeline_state_id,
            user_id=current_user.id,
            activity_type=PipelineActivityType.INTERVIEW_SCHEDULED,
            details={
                "interview_id": str(session.id),
                "job_position": request.job_position,
                "interview_type": request.interview_type,
                "interview_category": request.interview_category,
                "scheduled_at": session.scheduled_at.isoformat() if session.scheduled_at else None
            }
        )
        db.add(activity)
        logger.info(f"Interview scheduled for candidate, but NOT moving to Interview stage yet")

# For update_interview_session endpoint - Add stage movement when interview STARTS
# Add this after line 359 where it checks for IN_PROGRESS status:

        if update_dict["status"] == InterviewStatus.IN_PROGRESS and not session.started_at:
            session.started_at = datetime.utcnow()
            
            # Move to Interview stage when interview actually starts
            if session.pipeline_state_id:
                logger.info(f"Interview starting - moving candidate to Interview stage")
                
                from app.models import CandidatePipelineState
                pipeline_state_result = await db.execute(
                    select(CandidatePipelineState).where(
                        CandidatePipelineState.id == session.pipeline_state_id
                    )
                )
                pipeline_state = pipeline_state_result.scalar_one_or_none()
                
                if pipeline_state and pipeline_state.current_stage_id != "interview":
                    old_stage = pipeline_state.current_stage_id
                    logger.info(f"Moving candidate from {old_stage} to interview stage")
                    
                    # Calculate time in previous stage
                    time_in_stage = int((datetime.utcnow() - pipeline_state.entered_stage_at).total_seconds())
                    
                    # Update the stage
                    pipeline_state.time_in_stage_seconds = time_in_stage
                    pipeline_state.current_stage_id = "interview"
                    pipeline_state.entered_stage_at = datetime.utcnow()
                    pipeline_state.updated_at = datetime.utcnow()
                    
                    # Create stage change activity
                    stage_activity = PipelineActivity(
                        candidate_id=pipeline_state.candidate_id,
                        pipeline_state_id=pipeline_state.id,
                        user_id=current_user.id,
                        activity_type=PipelineActivityType.STAGE_CHANGED,
                        from_stage_id=old_stage,
                        to_stage_id="interview",
                        details={
                            "reason": "Interview started - automatically moved to Interview stage",
                            "time_in_previous_stage": time_in_stage,
                            "interview_id": str(session.id)
                        }
                    )
                    db.add(stage_activity)
                    logger.info(f"Stage updated from {old_stage} to interview")