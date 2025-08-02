"""Fixed interview completion endpoint with proper pipeline integration"""

# This code should replace the section in update_interview_session endpoint
# after line 376 where it checks for completed interview

if session.pipeline_state_id and "status" in update_dict and update_dict["status"] == InterviewStatus.COMPLETED:
    logger.info(f"Processing completed interview - rating: {session.overall_rating}, recommendation: {session.recommendation}")
    
    # Create activity for interview completion
    activity = PipelineActivity(
        candidate_id=session.resume_id,
        pipeline_state_id=session.pipeline_state_id,
        user_id=current_user.id,
        activity_type=PipelineActivityType.INTERVIEW_COMPLETED,
        details={
            "interview_id": str(session.id),
            "job_position": session.job_position,
            "interview_type": session.interview_type,
            "interview_category": session.interview_category,
            "overall_rating": session.overall_rating,
            "recommendation": session.recommendation,
            "duration_minutes": session.duration_minutes
        }
    )
    db.add(activity)
    
    # Handle pipeline stage transition directly here
    if session.overall_rating or session.recommendation:
        logger.info(f"Checking pipeline state transition for rating: {session.overall_rating}, recommendation: {session.recommendation}")
        
        # Get current pipeline state
        from app.models import CandidatePipelineState
        pipeline_state_result = await db.execute(
            select(CandidatePipelineState).where(
                CandidatePipelineState.id == session.pipeline_state_id
            )
        )
        pipeline_state = pipeline_state_result.scalar_one_or_none()
        
        if pipeline_state and pipeline_state.current_stage_id == "interview":
            # Determine next stage based on interview outcome
            next_stage = None
            reason = ""
            
            if session.recommendation == "hire" or (session.overall_rating and session.overall_rating >= 4):
                next_stage = "offer"
                reason = f"Interview completed with positive outcome - Rating: {session.overall_rating}/5, Recommendation: {session.recommendation}"
                logger.info(f"Moving candidate to offer stage - rating: {session.overall_rating}, recommendation: {session.recommendation}")
            elif session.recommendation == "no_hire" or (session.overall_rating and session.overall_rating <= 2):
                next_stage = "rejected"
                reason = f"Interview completed with negative outcome - Rating: {session.overall_rating}/5, Recommendation: {session.recommendation}"
                logger.info(f"Moving candidate to rejected stage - rating: {session.overall_rating}, recommendation: {session.recommendation}")
            else:
                logger.info(f"No clear decision - rating: {session.overall_rating}, recommendation: {session.recommendation}, keeping in interview stage")
            
            if next_stage:
                old_stage = pipeline_state.current_stage_id
                logger.info(f"Moving candidate from {old_stage} to {next_stage}")
                
                # Calculate time in interview stage
                time_in_stage = int((datetime.utcnow() - pipeline_state.entered_stage_at).total_seconds())
                
                # Update the stage directly
                pipeline_state.time_in_stage_seconds = time_in_stage
                pipeline_state.current_stage_id = next_stage
                pipeline_state.entered_stage_at = datetime.utcnow()
                pipeline_state.updated_at = datetime.utcnow()
                
                # Handle rejection/offer specific fields
                if next_stage == "rejected":
                    pipeline_state.rejection_reason = reason
                
                # Create stage change activity
                stage_activity = PipelineActivity(
                    candidate_id=pipeline_state.candidate_id,
                    pipeline_state_id=pipeline_state.id,
                    user_id=current_user.id,
                    activity_type=PipelineActivityType.STAGE_CHANGED,
                    from_stage_id=old_stage,
                    to_stage_id=next_stage,
                    details={
                        "reason": reason,
                        "time_in_previous_stage": time_in_stage,
                        "interview_id": str(session.id),
                        "interview_rating": session.overall_rating,
                        "interview_recommendation": session.recommendation
                    }
                )
                db.add(stage_activity)
                
                logger.info(f"Stage updated from {old_stage} to {next_stage}")
        else:
            if pipeline_state:
                logger.info(f"Candidate in {pipeline_state.current_stage_id} stage, not in interview stage")
            else:
                logger.error(f"Pipeline state {session.pipeline_state_id} not found!")
    else:
        logger.info("No rating or recommendation provided, skipping pipeline update")
else:
    logger.info(f"Not processing pipeline update - pipeline_state_id: {session.pipeline_state_id}, status: {update_dict.get('status')}")

# Single commit for everything
await db.commit()
await db.refresh(session)