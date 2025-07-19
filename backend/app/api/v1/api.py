"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, resumes, search, users, interviews, interview_pipelines, websocket, linkedin, debug_search, debug_profiles, search_debug, debug_skills, fix_data, debug_duplicates, admin, bulk_import, debug, cleanup, linkedin_fix, outreach, admin_migrate

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
api_router.include_router(linkedin_fix.router, prefix="/linkedin-fix", tags=["linkedin-fix"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(debug_search.router, prefix="/debug", tags=["debug"])
api_router.include_router(debug_profiles.router, prefix="/debug-profiles", tags=["debug"])
api_router.include_router(search_debug.router, prefix="/search-debug", tags=["search-debug"])
api_router.include_router(debug_skills.router, prefix="/debug-skills", tags=["debug-skills"])
api_router.include_router(fix_data.router, prefix="/fix-data", tags=["fix-data"])
api_router.include_router(debug_duplicates.router, prefix="/debug-duplicates", tags=["debug-duplicates"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(bulk_import.router, prefix="/bulk-import", tags=["bulk-import"])
api_router.include_router(debug.router, prefix="/debug-system", tags=["debug-system"])
api_router.include_router(cleanup.router, prefix="/cleanup", tags=["cleanup"])
api_router.include_router(outreach.router, prefix="/outreach", tags=["outreach"])
api_router.include_router(admin_migrate.router, prefix="/admin/migrate", tags=["admin"])
# Analytics temporarily disabled due to import issues
# api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])