"""Outreach message generation endpoints."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Integer, cast
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models import User, OutreachMessage, OutreachTemplate, MessageStyle, MessageStatus, EventType
from app.schemas.outreach import (
    OutreachMessageGenerate,
    OutreachMessageGenerateResponse,
    OutreachMessageDB,
    OutreachTemplateCreate,
    OutreachTemplateResponse,
    MessagePerformanceTrack,
    OutreachAnalytics
)
from app.services.outreach import OutreachService
from app.services.analytics import analytics_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=OutreachMessageGenerateResponse)
async def generate_outreach_messages(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    message_request: OutreachMessageGenerate
) -> OutreachMessageGenerateResponse:
    """Generate personalized outreach messages for a candidate.
    
    This endpoint generates three variations of outreach messages:
    - Casual: Friendly and conversational
    - Professional: Formal and business-oriented
    - Technical: Domain-specific with technical depth
    
    The messages are personalized based on the candidate's profile and the job requirements.
    """
    try:
        # Clean up job_requirements if it's a string "null"
        job_requirements = message_request.job_requirements
        if job_requirements and isinstance(job_requirements, str) and job_requirements.lower() == "null":
            job_requirements = None
        
        service = OutreachService()
        result = await service.generate_messages(
            db=db,
            user_id=current_user.id,
            resume_id=message_request.resume_id,
            job_title=message_request.job_title,
            company_name=message_request.company_name,
            job_requirements=job_requirements,
            custom_instructions=message_request.custom_instructions
        )
        
        return OutreachMessageGenerateResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating outreach messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate messages")


@router.get("/messages", response_model=List[OutreachMessageDB])
async def get_outreach_messages(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    resume_id: Optional[UUID] = None,
    status: Optional[MessageStatus] = None,
    style: Optional[MessageStyle] = None
) -> List[OutreachMessageDB]:
    """Get outreach messages with optional filters."""
    query = select(OutreachMessage).where(
        OutreachMessage.user_id == current_user.id
    )
    
    if resume_id:
        query = query.where(OutreachMessage.resume_id == resume_id)
    if status:
        query = query.where(OutreachMessage.status == status)
    if style:
        query = query.where(OutreachMessage.style == style)
    
    query = query.order_by(OutreachMessage.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return [OutreachMessageDB.from_orm(msg) for msg in messages]


@router.post("/track", response_model=dict)
async def track_message_performance(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    tracking_data: MessagePerformanceTrack
) -> dict:
    """Track performance events for outreach messages."""
    # Verify the message belongs to the current user
    result = await db.execute(
        select(OutreachMessage).where(
            OutreachMessage.id == tracking_data.message_id,
            OutreachMessage.user_id == current_user.id
        )
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    service = OutreachService()
    success = await service.track_message_performance(
        db=db,
        message_id=tracking_data.message_id,
        event=tracking_data.event,
        metadata=tracking_data.metadata
    )
    
    return {"success": success}


@router.get("/analytics", response_model=OutreachAnalytics)
async def get_outreach_analytics(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    days: int = Query(30, ge=1, le=365)
) -> OutreachAnalytics:
    """Get analytics for outreach message performance."""
    # This is a simplified version - you'd want more sophisticated analytics
    from datetime import datetime, timedelta
    
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get message counts by status
    result = await db.execute(
        select(
            func.count(OutreachMessage.id).label("total"),
            func.sum(cast(OutreachMessage.status == MessageStatus.SENT, Integer)).label("sent"),
            func.sum(cast(OutreachMessage.status == MessageStatus.OPENED, Integer)).label("opened"),
            func.sum(cast(OutreachMessage.status == MessageStatus.RESPONDED, Integer)).label("responded")
        ).where(
            OutreachMessage.user_id == current_user.id,
            OutreachMessage.created_at >= since_date
        )
    )
    stats = result.first()
    
    total = stats.total or 0
    sent = stats.sent or 0
    opened = stats.opened or 0
    responded = stats.responded or 0
    
    response_rate = (responded / sent * 100) if sent > 0 else 0
    
    # Get performance by style
    style_stats = {}
    for style in MessageStyle:
        result = await db.execute(
            select(
                func.count(OutreachMessage.id).label("total"),
                func.sum(cast(OutreachMessage.status == MessageStatus.RESPONDED, Integer)).label("responded")
            ).where(
                OutreachMessage.user_id == current_user.id,
                OutreachMessage.style == style,
                OutreachMessage.created_at >= since_date
            )
        )
        style_data = result.first()
        
        style_total = style_data.total or 0
        style_responded = style_data.responded or 0
        
        style_stats[style.value] = {
            "total": style_total,
            "responded": style_responded,
            "response_rate": (style_responded / style_total * 100) if style_total > 0 else 0
        }
    
    # Determine best performing style
    best_style = None
    best_rate = 0
    for style, data in style_stats.items():
        if data["response_rate"] > best_rate and data["total"] > 5:  # Min 5 messages
            best_style = style
            best_rate = data["response_rate"]
    
    return OutreachAnalytics(
        total_messages=total,
        messages_sent=sent,
        messages_opened=opened,
        messages_responded=responded,
        overall_response_rate=response_rate,
        avg_response_time_hours=None,  # Would need to calculate from timestamps
        best_performing_style=MessageStyle(best_style) if best_style else None,
        best_performing_time=None,  # Would need more sophisticated analysis
        by_style=style_stats
    )


@router.post("/templates", response_model=OutreachTemplateResponse)
async def create_outreach_template(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    template: OutreachTemplateCreate
) -> OutreachTemplateResponse:
    """Create a new outreach template."""
    db_template = OutreachTemplate(
        user_id=current_user.id,
        **template.dict()
    )
    db.add(db_template)
    await db.commit()
    await db.refresh(db_template)
    
    return OutreachTemplateResponse.from_orm(db_template)


@router.get("/templates", response_model=List[OutreachTemplateResponse])
async def get_outreach_templates(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    include_public: bool = Query(True),
    style: Optional[MessageStyle] = None,
    industry: Optional[str] = None,
    role_level: Optional[str] = None
) -> List[OutreachTemplateResponse]:
    """Get outreach templates with optional filters."""
    query = select(OutreachTemplate)
    
    # Get user's own templates and optionally public ones
    if include_public:
        query = query.where(
            (OutreachTemplate.user_id == current_user.id) |
            (OutreachTemplate.is_public == True)
        )
    else:
        query = query.where(OutreachTemplate.user_id == current_user.id)
    
    if style:
        query = query.where(OutreachTemplate.style == style)
    if industry:
        query = query.where(OutreachTemplate.industry == industry)
    if role_level:
        query = query.where(OutreachTemplate.role_level == role_level)
    
    query = query.order_by(OutreachTemplate.avg_response_rate.desc().nullslast())
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [OutreachTemplateResponse.from_orm(tmpl) for tmpl in templates]