#!/usr/bin/env python3
"""Test script to verify pipeline stage movement fix"""

import asyncio
import logging
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import CandidatePipelineState, InterviewSession, PipelineActivity, Resume
from app.models.pipeline import PipelineActivityType
from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pipeline_movement():
    """Test if pipeline stages are moving correctly"""
    
    # Create database connection
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Test 1: Check Brian Williams current state
        logger.info("=== Test 1: Checking Brian Williams ===")
        brian_result = await db.execute(
            select(Resume).where(
                Resume.first_name == "Brian",
                Resume.last_name == "Williams"
            ).order_by(Resume.created_at.desc())
        )
        brian = brian_result.scalar()
        
        if brian:
            logger.info(f"Found Brian Williams: {brian.id}")
            
            # Get his pipeline state
            ps_result = await db.execute(
                select(CandidatePipelineState).where(
                    CandidatePipelineState.candidate_id == brian.id,
                    CandidatePipelineState.is_active == True
                )
            )
            pipeline_state = ps_result.scalar_one_or_none()
            
            if pipeline_state:
                logger.info(f"Brian's current stage: {pipeline_state.current_stage_id}")
                logger.info(f"Pipeline state ID: {pipeline_state.id}")
                
                # Check interviews
                i_result = await db.execute(
                    select(InterviewSession).where(
                        InterviewSession.resume_id == brian.id
                    ).order_by(InterviewSession.created_at.desc())
                )
                interviews = i_result.scalars().all()
                
                for interview in interviews:
                    logger.info(f"Interview {interview.id}: status={interview.status}, rating={interview.overall_rating}, pipeline_state_id={interview.pipeline_state_id}")
        
        # Test 2: Check Michelle Garcia
        logger.info("\n=== Test 2: Checking Michelle Garcia ===")
        michelle_result = await db.execute(
            select(Resume).where(
                Resume.first_name == "Michelle",
                Resume.last_name == "Garcia"
            ).order_by(Resume.created_at.desc())
        )
        michelle = michelle_result.scalar()
        
        if michelle:
            logger.info(f"Found Michelle Garcia: {michelle.id}")
            
            # Get her pipeline state
            ps_result = await db.execute(
                select(CandidatePipelineState).where(
                    CandidatePipelineState.candidate_id == michelle.id,
                    CandidatePipelineState.is_active == True
                )
            )
            pipeline_state = ps_result.scalar_one_or_none()
            
            if pipeline_state:
                logger.info(f"Michelle's current stage: {pipeline_state.current_stage_id}")
                logger.info(f"Pipeline state ID: {pipeline_state.id}")
        
        # Test 3: Check recent activities
        logger.info("\n=== Test 3: Recent Pipeline Activities ===")
        activities_result = await db.execute(
            select(PipelineActivity).where(
                PipelineActivity.activity_type.in_([
                    PipelineActivityType.STAGE_CHANGED,
                    PipelineActivityType.INTERVIEW_SCHEDULED
                ])
            ).order_by(PipelineActivity.created_at.desc()).limit(10)
        )
        activities = activities_result.scalars().all()
        
        for activity in activities:
            logger.info(f"Activity: {activity.activity_type.value} - from {activity.from_stage_id} to {activity.to_stage_id} - {activity.created_at}")

if __name__ == "__main__":
    asyncio.run(test_pipeline_movement())