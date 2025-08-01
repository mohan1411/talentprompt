"""Main FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.redis import get_redis_client, close_redis
from app.middleware.analytics import AnalyticsMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    try:
        await get_redis_client()
        print("Redis connection established")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        print("Continuing without Redis - some features may be limited")
        # Don't raise in production - Redis is optional
    
    yield
    
    # Shutdown
    await close_redis()
    print("Redis connection closed")


# Conditionally enable API documentation
docs_url = "/docs" if settings.ENVIRONMENT != "production" else None
redoc_url = "/redoc" if settings.ENVIRONMENT != "production" else None
openapi_url = f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan,
)

# Import shared limiter instance
from app.core.limiter import limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# Force Railway redeploy - 2025-01-18

# Log startup configuration
print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
print(f"Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
print(f"DATABASE_URL present: {'DATABASE_URL' in os.environ}")
print(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
print(f"CORS Origins from env: {os.environ.get('BACKEND_CORS_ORIGINS', 'Not set')}")

# Critical CORS check for production
if os.environ.get('RAILWAY_ENVIRONMENT') == 'production':
    cors_str = str(settings.BACKEND_CORS_ORIGINS)
    if 'promtitude.com' not in cors_str:
        print("WARNING: promtitude.com not in CORS origins! Frontend will be blocked!")
        print("Set BACKEND_CORS_ORIGINS environment variable to fix this")
    else:
        print("✓ CORS configured correctly for promtitude.com")

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    # Handle both with and without trailing slashes
    origins = []
    for origin in settings.BACKEND_CORS_ORIGINS:
        origin_str = str(origin).rstrip('/')
        origins.append(origin_str)
        origins.append(f"{origin_str}/")
    
    # Chrome extensions need special handling
    def is_allowed_origin(origin: str) -> bool:
        # Check if it's in our explicit list
        if origin in origins:
            return True
        # Allow any Chrome extension origin
        if origin and origin.startswith("chrome-extension://"):
            return True
        return False
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origin_regex="chrome-extension://.*"  # Allow all Chrome extensions
    )

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # HSTS for production
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.google.com https://www.gstatic.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://www.google.com; "
        "frame-src 'self' https://www.google.com; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )
    response.headers["Content-Security-Policy"] = csp
    
    # Note: Server header cannot be removed via middleware in FastAPI
    # It's set by the ASGI server (uvicorn) - use --header server:Promtitude when running uvicorn
    
    # Cache control for auth endpoints
    if request.url.path.startswith("/api/v1/auth"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    return response

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# Add analytics middleware
app.add_middleware(AnalyticsMiddleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    print(f"Startup event - Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
    
    # Always try to create tables if they don't exist
    try:
        from app.api.v1.dependencies.database import get_db
        from sqlalchemy import text
        
        async for db in get_db():
            # Check if all required tables exist
            result = await db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name IN ('outreach_messages', 'analytics_events', 'candidate_submissions', 'invitation_campaigns')
            """))
            existing_tables = [row[0] for row in result]
            
            # Create submission tables if missing
            if 'candidate_submissions' not in existing_tables or 'invitation_campaigns' not in existing_tables:
                print("Creating missing submission tables...")
                try:
                    # Create invitation_campaigns first
                    await db.execute(text("""
                        CREATE TABLE IF NOT EXISTS invitation_campaigns (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            recruiter_id UUID NOT NULL,
                            name VARCHAR(255) NOT NULL,
                            description TEXT,
                            source_type VARCHAR(50),
                            source_data JSONB,
                            is_public BOOLEAN DEFAULT FALSE,
                            public_slug VARCHAR(100),
                            email_template TEXT,
                            expires_in_days INTEGER DEFAULT 7,
                            branding JSONB,
                            auto_close_date TIMESTAMP,
                            max_submissions INTEGER,
                            stats JSONB DEFAULT '{}',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    
                    # Then create candidate_submissions
                    await db.execute(text("""
                        CREATE TABLE IF NOT EXISTS candidate_submissions (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            token VARCHAR(255) UNIQUE NOT NULL,
                            submission_type VARCHAR(10) NOT NULL,
                            status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                            recruiter_id UUID NOT NULL,
                            campaign_id UUID,
                            resume_id UUID,
                            email VARCHAR(255) NOT NULL,
                            first_name VARCHAR(100),
                            last_name VARCHAR(100),
                            phone VARCHAR(50),
                            linkedin_url VARCHAR(255),
                            availability VARCHAR(50),
                            salary_expectations JSONB,
                            location_preferences JSONB,
                            resume_file_url VARCHAR(500),
                            resume_text TEXT,
                            parsed_data JSONB,
                            email_sent_at TIMESTAMP,
                            email_opened_at TIMESTAMP,
                            link_clicked_at TIMESTAMP,
                            submitted_at TIMESTAMP,
                            processed_at TIMESTAMP,
                            expires_at TIMESTAMP NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    
                    # Create indexes
                    await db.execute(text("CREATE INDEX IF NOT EXISTS ix_candidate_submissions_token ON candidate_submissions(token)"))
                    await db.execute(text("CREATE INDEX IF NOT EXISTS ix_candidate_submissions_recruiter_id ON candidate_submissions(recruiter_id)"))
                    await db.execute(text("CREATE INDEX IF NOT EXISTS ix_candidate_submissions_email ON candidate_submissions(email)"))
                    
                    # Only commit if we're in a transaction
                    try:
                        await db.commit()
                    except Exception:
                        pass  # No transaction to commit
                    
                    print("✅ Submission tables created successfully!")
                    
                except Exception as e:
                    print(f"Error creating submission tables: {e}")
                    try:
                        await db.rollback()
                    except Exception:
                        pass  # No transaction to rollback
            
            if 'analytics_events' not in existing_tables:
                print("analytics_events table not found - creating analytics table...")
                
                # Read and execute SQL file
                sql_path = os.path.join(os.path.dirname(__file__), "..", "create_outreach_tables.sql")
                if os.path.exists(sql_path):
                    with open(sql_path, "r") as f:
                        sql = f.read()
                    
                    # Execute each statement separately
                    statements = [s.strip() for s in sql.split(';') if s.strip()]
                    for statement in statements:
                        if statement:
                            try:
                                await db.execute(text(statement))
                            except Exception as e:
                                print(f"Statement error (continuing): {e}")
                    
                    await db.commit()
                    print("Tables created successfully!")
                else:
                    print(f"SQL file not found at {sql_path}")
            else:
                print("outreach_messages table already exists")
            break
    except Exception as e:
        print(f"Startup database check failed: {e}")
        # Don't fail startup, let the app continue


@app.get("/")
async def root():
    """Root endpoint."""
    import sys
    print("\n[ROOT ENDPOINT] Request received", flush=True)
    sys.stdout.flush()
    return {
        "message": "Welcome to Promtitude API",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/test-email-debug")
async def test_email_debug():
    """Test endpoint to debug email output."""
    import sys
    print("\n" + "="*80, flush=True)
    print("[TEST EMAIL DEBUG] Endpoint called", flush=True)
    print("="*80, flush=True)
    sys.stdout.flush()
    
    # Test the email service directly
    from app.services.email_service_production import email_service
    
    print(f"Email service type: {type(email_service).__name__}", flush=True)
    print(f"Email service module: {email_service.__module__}", flush=True)
    
    # Send a test email
    result = await email_service.send_email(
        to_email="test@example.com",
        subject="Test Debug Email",
        html_content="<p>This is a test</p>",
        text_content="This is a test"
    )
    
    print(f"Email send result: {result}", flush=True)
    print("="*80 + "\n", flush=True)
    sys.stdout.flush()
    
    return {
        "status": "Test complete",
        "email_service_type": type(email_service).__name__,
        "email_service_module": email_service.__module__,
        "result": result
    }


@app.post("/api/v1/test-smtp-email")
async def test_smtp_email(email: str):
    """Test SMTP email configuration with a real email address."""
    from app.services.email_service_production import email_service
    from app.core.config import settings
    
    result = {
        "email_service_type": type(email_service).__name__,
        "smtp_configured": bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD),
        "smtp_host": settings.SMTP_HOST or "Not configured",
        "test_sent": False,
        "invitation_sent": False,
        "errors": []
    }
    
    # Only test if SMTP is configured
    if result["smtp_configured"] and hasattr(email_service, 'send_test_email'):
        try:
            # Send test email
            test_result = await email_service.send_test_email(email)
            result["test_sent"] = test_result
            
            # Send sample invitation
            invitation_result = await email_service.send_submission_invitation(
                to_email=email,
                candidate_name="Test Candidate",
                recruiter_name="Your Name",
                submission_link=f"{settings.FRONTEND_URL}/submit/test_token_demo",
                message="This is a test invitation email to verify the formatting looks correct.",
                deadline_days=7,
                company_name="Promtitude Demo",
                is_update=False
            )
            result["invitation_sent"] = invitation_result
            
        except Exception as e:
            result["errors"].append(str(e))
    else:
        result["errors"].append("SMTP not configured or email service doesn't support test emails")
    
    return result


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint for Railway."""
    from app.api.v1.dependencies.database import get_db
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "service": "promtitude-api",
        "version": settings.VERSION,
        "docs": "/docs",
        "database": "unknown",
        "vector_search": "unknown"
    }
    
    # Test database connection
    try:
        async for db in get_db():
            result = await db.execute(text("SELECT 1"))
            if result.scalar() == 1:
                health_status["database"] = "connected"
            break
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Test Qdrant connection
    try:
        from app.services.vector_search import vector_search
        collection_info = await vector_search.get_collection_info()
        if collection_info.get("status") == "connected":
            health_status["vector_search"] = f"connected ({collection_info.get('points_count', 0)} vectors)"
        else:
            health_status["vector_search"] = f"error: {collection_info.get('error', 'Unknown error')}"
    except Exception as e:
        health_status["vector_search"] = f"error: {str(e)}"
    
    return health_status


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}


@app.get("/api/v1/analytics/test")
async def test_analytics_endpoint():
    """Test analytics endpoint."""
    return {"status": "Analytics test endpoint working"}


@app.get("/api/v1/analytics/basic-stats")
async def get_basic_analytics_stats():
    """Get basic analytics statistics with real data."""
    from app.api.v1.dependencies.database import get_db
    from sqlalchemy import text, select, func
    from app.models import User, Resume
    
    stats = {
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
    
    try:
        async for db in get_db():
            # Get total users
            user_count = await db.execute(select(func.count(User.id)))
            stats["total_users"] = user_count.scalar() or 0
            
            # Get total resumes
            resume_count = await db.execute(select(func.count(Resume.id)))
            stats["total_resumes"] = resume_count.scalar() or 0
            
            # Get recent analytics events count
            analytics_count = await db.execute(text("""
                SELECT COUNT(*) FROM analytics_events 
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """))
            stats["api_performance"]["total_requests"] = analytics_count.scalar() or 0
            
            break
    except Exception as e:
        print(f"Error getting analytics stats: {e}")
    
    return stats


@app.get("/api/v1/migrate")
async def run_migrations():
    """Run database migrations - useful for production deployments."""
    from app.api.v1.dependencies.database import get_db
    from sqlalchemy import text
    
    results = {
        "status": "starting",
        "tables_created": False,
        "error": None,
        "tables_check": None
    }
    
    try:
        async for db in get_db():
            # First check if tables exist
            check_result = await db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('outreach_messages', 'outreach_templates')
            """))
            existing_tables = [row[0] for row in check_result]
            
            if 'outreach_messages' not in existing_tables or 'analytics_events' not in existing_tables:
                print("Creating outreach tables...")
                
                # Create enum types
                try:
                    await db.execute(text("""
                        DO $$ BEGIN
                            CREATE TYPE messagestyle AS ENUM ('casual', 'professional', 'technical');
                        EXCEPTION
                            WHEN duplicate_object THEN null;
                        END $$;
                    """))
                    await db.execute(text("""
                        DO $$ BEGIN
                            CREATE TYPE messagestatus AS ENUM ('generated', 'sent', 'opened', 'responded', 'not_interested');
                        EXCEPTION
                            WHEN duplicate_object THEN null;
                        END $$;
                    """))
                except Exception as e:
                    print(f"Enum creation warning: {e}")
                
                # Create outreach_messages table
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS outreach_messages (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES users(id),
                        resume_id UUID NOT NULL REFERENCES resumes(id),
                        subject VARCHAR(255) NOT NULL,
                        body TEXT NOT NULL,
                        style messagestyle NOT NULL,
                        job_title VARCHAR(255),
                        job_requirements JSON,
                        company_name VARCHAR(255),
                        status messagestatus DEFAULT 'generated',
                        sent_at TIMESTAMP,
                        opened_at TIMESTAMP,
                        responded_at TIMESTAMP,
                        quality_score FLOAT,
                        response_rate FLOAT,
                        generation_prompt TEXT,
                        model_version VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create analytics_events table
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS analytics_events (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                        event_type VARCHAR(50) NOT NULL,
                        event_data JSONB,
                        ip_address VARCHAR(45),
                        user_agent VARCHAR(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create indexes
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_messages_user_id ON outreach_messages(user_id)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_messages_resume_id ON outreach_messages(resume_id)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_messages_status ON outreach_messages(status)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_messages_created_at ON outreach_messages(created_at)"))
                
                # Create analytics indexes
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics_events(user_id)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events(event_type)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events(created_at)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_analytics_events_type_date ON analytics_events(event_type, created_at)"))
                
                # Create outreach_templates table
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS outreach_templates (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES users(id),
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        subject_template VARCHAR(500),
                        body_template TEXT NOT NULL,
                        style messagestyle NOT NULL,
                        industry VARCHAR(100),
                        role_level VARCHAR(50),
                        job_function VARCHAR(100),
                        times_used INTEGER DEFAULT 0,
                        avg_response_rate FLOAT,
                        is_public BOOLEAN DEFAULT false,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create indexes for templates
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_templates_user_id ON outreach_templates(user_id)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_templates_is_public ON outreach_templates(is_public)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_templates_style ON outreach_templates(style)"))
                
                await db.commit()
                results["tables_created"] = True
                results["status"] = "completed"
            else:
                results["status"] = "tables_already_exist"
            
            # Final check
            final_check = await db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('outreach_messages', 'outreach_templates')
            """))
            results["tables_check"] = [row[0] for row in final_check]
            break
            
    except Exception as e:
        results["error"] = str(e)
        results["status"] = "failed"
    
    return results