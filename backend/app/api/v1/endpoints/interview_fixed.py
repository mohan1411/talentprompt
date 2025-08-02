"""Fixed interview endpoint with proper pipeline integration"""

# Add this code to the prepare_interview endpoint after creating the interview session

# This is the fixed section for moving candidate to interview stage
if request.pipeline_state_id:
    logger.info(f"Processing pipeline integration for pipeline_state_id: {request.pipeline_state_id}")
    
    # Create activity
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
    
    # Direct update without calling the service (to avoid nested commits)
    try:
        # Get current pipeline state
        pipeline_state_result = await db.execute(
            select(CandidatePipelineState).where(
                CandidatePipelineState.id == request.pipeline_state_id
            )
        )
        pipeline_state = pipeline_state_result.scalar_one_or_none()
        
        if pipeline_state and pipeline_state.current_stage_id != "interview":
            old_stage = pipeline_state.current_stage_id
            logger.info(f"Moving candidate from {old_stage} to interview stage")
            
            # Calculate time in previous stage
            time_in_stage = int((datetime.utcnow() - pipeline_state.entered_stage_at).total_seconds())
            
            # Update the stage directly
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
                    "reason": "Interview scheduled - automatically moved to Interview stage",
                    "time_in_previous_stage": time_in_stage
                }
            )
            db.add(stage_activity)
            
            logger.info(f"Stage updated from {old_stage} to interview")
        else:
            if pipeline_state:
                logger.info(f"Candidate already in {pipeline_state.current_stage_id} stage, not moving")
            else:
                logger.error(f"Pipeline state {request.pipeline_state_id} not found!")
    except Exception as e:
        logger.error(f"Error moving candidate to interview stage: {str(e)}", exc_info=True)
        # Don't fail the entire request if stage movement fails
        
# Single commit for everything
await db.commit()
await db.refresh(session)