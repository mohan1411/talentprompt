"""Analytics middleware for tracking API requests."""
import time
from typing import Callable
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.services.analytics import analytics_service
from app.models import EventType
from app.core.logging import logger


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware to track API requests for analytics."""
    
    # Endpoints to exclude from tracking
    EXCLUDED_PATHS = {
        "/",
        "/health",
        "/api/v1/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track analytics."""
        # Skip tracking for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # Skip tracking for static files
        if request.url.path.startswith("/static/"):
            return await call_next(request)
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Track analytics event asynchronously
        try:
            # Get user ID from request state if authenticated
            user_id = None
            if hasattr(request.state, "user_id"):
                user_id = request.state.user_id
            
            # Get client info
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent", "")[:500]  # Limit length
            
            # Prepare event data
            event_data = {
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "response_time": round(response_time, 2),
            }
            
            # Add query parameters for search tracking
            if request.url.path == "/api/v1/search" and request.query_params.get("q"):
                event_data["query"] = request.query_params.get("q")
            
            # Use session maker to get DB session
            async with async_session_maker() as db:
                await analytics_service.track_event(
                    db=db,
                    event_type=EventType.API_REQUEST,
                    event_data=event_data,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    wait_for_commit=False  # Fire and forget
                )
                
        except Exception as e:
            # Don't let analytics errors affect the response
            logger.error(f"Analytics middleware error: {str(e)}")
        
        return response


def track_event_handler(
    event_type: str,
    extract_data: Callable[[Request], dict] = None
):
    """
    Decorator for tracking specific events in route handlers.
    
    Usage:
        @router.post("/upload")
        @track_event_handler(EventType.RESUME_UPLOADED)
        async def upload_resume(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(request: Request, *args, **kwargs):
            # Execute the original function
            result = await func(request, *args, **kwargs)
            
            # Track the event
            try:
                # Extract user ID if available
                user_id = None
                if hasattr(request.state, "user_id"):
                    user_id = request.state.user_id
                
                # Extract event data
                event_data = {}
                if extract_data:
                    event_data = extract_data(request)
                
                # Get client info
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent", "")[:500]
                
                async with async_session_maker() as db:
                    await analytics_service.track_event(
                        db=db,
                        event_type=event_type,
                        event_data=event_data,
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        wait_for_commit=False
                    )
            except Exception as e:
                logger.error(f"Event tracking error: {str(e)}")
            
            return result
        
        return wrapper
    return decorator