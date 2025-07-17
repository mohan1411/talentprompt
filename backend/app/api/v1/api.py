"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, resumes, search, users, interviews, interview_pipelines, websocket, linkedin, debug_search

api_router = APIRouter()

# Include routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
api_router.include_router(interview_pipelines.router, prefix="/pipelines", tags=["pipelines"])
api_router.include_router(linkedin.router, prefix="/linkedin", tags=["linkedin"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(debug_search.router, prefix="/debug", tags=["debug"])