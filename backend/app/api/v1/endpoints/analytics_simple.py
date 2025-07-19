"""Simple analytics endpoints to test."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/test")
async def test_analytics():
    """Test endpoint to verify analytics routes are working."""
    return {"status": "Analytics endpoint is working", "endpoint": "simple"}


@router.get("/basic-stats")
async def get_basic_stats():
    """Get basic analytics statistics."""
    return {
        "daily_active_users": [],
        "feature_usage": {},
        "popular_searches": [],
        "api_performance": {
            "total_requests": 0,
            "avg_response_time_ms": 0,
            "requests_per_hour": 0,
            "top_endpoints": []
        },
        "total_users": 0,
        "total_resumes": 0
    }