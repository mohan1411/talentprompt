"""Analytics endpoints."""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api import deps
from app.models import User, EventType
from app.services.analytics import analytics_service

router = APIRouter()


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


class TrackEventRequest(BaseModel):
    """Request model for tracking events."""
    event_type: str = Field(..., max_length=50)
    event_data: Optional[Dict[str, Any]] = None


class AnalyticsStatsResponse(BaseModel):
    """Response model for analytics statistics."""
    daily_active_users: List[Dict[str, Any]]
    feature_usage: Dict[str, int]
    popular_searches: List[Dict[str, Any]]
    api_performance: Dict[str, Any]
    total_users: int
    total_resumes: int


@router.post("/track", response_model=MessageResponse)
async def track_event(
    request: TrackEventRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user),
) -> MessageResponse:
    """Track an analytics event from the frontend."""
    # Get request info from FastAPI
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest
    
    # Note: In a real implementation, you'd get these from the request context
    ip_address = None
    user_agent = None
    
    await analytics_service.track_event(
        db=db,
        event_type=request.event_type,
        event_data=request.event_data,
        user_id=current_user.id if current_user else None,
        ip_address=ip_address,
        user_agent=user_agent,
        wait_for_commit=True
    )
    
    return MessageResponse(message="Event tracked successfully")


@router.get("/stats", response_model=AnalyticsStatsResponse)
async def get_analytics_stats(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
    days: int = Query(30, ge=1, le=365),
) -> AnalyticsStatsResponse:
    """Get analytics statistics (admin only)."""
    # Get various analytics
    daily_active_users = await analytics_service.get_daily_active_users(db, days=days)
    feature_usage = await analytics_service.get_feature_usage(db, days=days)
    popular_searches = await analytics_service.get_popular_searches(db, days=7, limit=10)
    api_performance = await analytics_service.get_api_performance(db, hours=24)
    
    # Get total counts
    from sqlalchemy import select, func
    from app.models import User, Resume
    
    total_users_query = select(func.count(User.id))
    total_users_result = await db.execute(total_users_query)
    total_users = total_users_result.scalar() or 0
    
    total_resumes_query = select(func.count(Resume.id))
    total_resumes_result = await db.execute(total_resumes_query)
    total_resumes = total_resumes_result.scalar() or 0
    
    return AnalyticsStatsResponse(
        daily_active_users=daily_active_users,
        feature_usage=feature_usage,
        popular_searches=popular_searches,
        api_performance=api_performance,
        total_users=total_users,
        total_resumes=total_resumes
    )


@router.get("/events")
async def get_recent_events(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = None,
    user_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Get recent analytics events (admin only)."""
    from sqlalchemy import select
    from app.models import AnalyticsEvent
    
    query = select(AnalyticsEvent).order_by(AnalyticsEvent.created_at.desc()).limit(limit)
    
    if event_type:
        query = query.where(AnalyticsEvent.event_type == event_type)
    if user_id:
        query = query.where(AnalyticsEvent.user_id == user_id)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    return [
        {
            "id": str(event.id),
            "event_type": event.event_type,
            "event_data": event.event_data,
            "user_id": str(event.user_id) if event.user_id else None,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]


@router.get("/user/{user_id}")
async def get_user_analytics(
    user_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
    days: int = Query(30, ge=1, le=365),
) -> Dict[str, Any]:
    """Get analytics for a specific user (admin only)."""
    return await analytics_service.get_user_analytics(db, user_id=user_id, days=days)