"""Analytics tracking service."""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, distinct
from sqlalchemy.orm import selectinload

from app.models import AnalyticsEvent, EventType, User

import logging
logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for tracking and querying analytics events."""
    
    @staticmethod
    async def track_event(
        db: AsyncSession,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        wait_for_commit: bool = False
    ) -> Optional[AnalyticsEvent]:
        """
        Track an analytics event.
        
        Args:
            db: Database session
            event_type: Type of event (use EventType constants)
            event_data: Additional event data
            user_id: ID of user who triggered event
            ip_address: Client IP address
            user_agent: Client user agent
            wait_for_commit: If False, returns immediately (fire-and-forget)
        
        Returns:
            Created event or None if fire-and-forget
        """
        try:
            event = AnalyticsEvent(
                event_type=event_type,
                event_data=event_data or {},
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(event)
            
            # Always commit immediately to avoid session issues
            await db.commit()
            
            if wait_for_commit:
                await db.refresh(event)
                return event
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to track analytics event: {str(e)}")
            try:
                await db.rollback()
            except:
                pass  # Session might already be closed
            return None
    
    @staticmethod
    async def get_event_counts(
        db: AsyncSession,
        event_types: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, int]:
        """Get event counts by type."""
        query = select(
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label('count')
        )
        
        # Apply filters
        filters = []
        if event_types:
            filters.append(AnalyticsEvent.event_type.in_(event_types))
        if start_date:
            filters.append(AnalyticsEvent.created_at >= start_date)
        if end_date:
            filters.append(AnalyticsEvent.created_at <= end_date)
        if user_id:
            filters.append(AnalyticsEvent.user_id == user_id)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.group_by(AnalyticsEvent.event_type)
        
        result = await db.execute(query)
        return {row.event_type: row.count for row in result}
    
    @staticmethod
    async def get_daily_active_users(
        db: AsyncSession,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily active users for the last N days."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(
            func.date(AnalyticsEvent.created_at).label('date'),
            func.count(distinct(AnalyticsEvent.user_id)).label('active_users')
        ).where(
            and_(
                AnalyticsEvent.created_at >= start_date,
                AnalyticsEvent.user_id.isnot(None)
            )
        ).group_by(
            func.date(AnalyticsEvent.created_at)
        ).order_by(
            func.date(AnalyticsEvent.created_at)
        )
        
        result = await db.execute(query)
        return [
            {
                'date': row.date.isoformat(),
                'active_users': row.active_users
            }
            for row in result
        ]
    
    @staticmethod
    async def get_popular_searches(
        db: AsyncSession,
        limit: int = 20,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get most popular search queries."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(AnalyticsEvent).where(
            and_(
                AnalyticsEvent.event_type == EventType.SEARCH_PERFORMED,
                AnalyticsEvent.created_at >= start_date
            )
        )
        
        result = await db.execute(query)
        events = result.scalars().all()
        
        # Count search queries
        search_counts = {}
        for event in events:
            if event.event_data and 'query' in event.event_data:
                query_text = event.event_data['query'].lower().strip()
                search_counts[query_text] = search_counts.get(query_text, 0) + 1
        
        # Sort and return top searches
        sorted_searches = sorted(
            search_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [
            {'query': query, 'count': count}
            for query, count in sorted_searches
        ]
    
    @staticmethod
    async def get_feature_usage(
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, int]:
        """Get feature usage statistics."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        feature_events = [
            EventType.SEARCH_PERFORMED,
            EventType.RESUME_UPLOADED,
            EventType.LINKEDIN_PROFILE_IMPORTED,
            EventType.OUTREACH_MESSAGE_GENERATED,
            EventType.INTERVIEW_STARTED
        ]
        
        return await AnalyticsService.get_event_counts(
            db,
            event_types=feature_events,
            start_date=start_date
        )
    
    @staticmethod
    async def get_api_performance(
        db: AsyncSession,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get API performance metrics."""
        start_date = datetime.utcnow() - timedelta(hours=hours)
        
        query = select(AnalyticsEvent).where(
            and_(
                AnalyticsEvent.event_type == EventType.API_REQUEST,
                AnalyticsEvent.created_at >= start_date
            )
        )
        
        result = await db.execute(query)
        events = result.scalars().all()
        
        # Calculate metrics
        total_requests = len(events)
        response_times = []
        endpoints = {}
        
        for event in events:
            if event.event_data:
                # Response time
                if 'response_time' in event.event_data:
                    response_times.append(event.event_data['response_time'])
                
                # Endpoint counts
                if 'endpoint' in event.event_data:
                    endpoint = event.event_data['endpoint']
                    endpoints[endpoint] = endpoints.get(endpoint, 0) + 1
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'total_requests': total_requests,
            'avg_response_time_ms': round(avg_response_time, 2),
            'requests_per_hour': round(total_requests / hours, 2),
            'top_endpoints': sorted(
                endpoints.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    @staticmethod
    async def get_user_analytics(
        db: AsyncSession,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for a specific user."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get event counts
        event_counts = await AnalyticsService.get_event_counts(
            db,
            user_id=user_id,
            start_date=start_date
        )
        
        # Get last activity
        query = select(AnalyticsEvent).where(
            AnalyticsEvent.user_id == user_id
        ).order_by(AnalyticsEvent.created_at.desc()).limit(1)
        
        result = await db.execute(query)
        last_event = result.scalar_one_or_none()
        
        return {
            'event_counts': event_counts,
            'total_events': sum(event_counts.values()),
            'last_activity': last_event.created_at.isoformat() if last_event else None
        }


analytics_service = AnalyticsService()