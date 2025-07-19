"""Main FastAPI application entry point."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)
# Force Railway redeploy - 2025-01-18

# Log startup configuration
print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
print(f"Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
print(f"DATABASE_URL present: {'DATABASE_URL' in os.environ}")
print(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    # Handle both with and without trailing slashes
    origins = []
    for origin in settings.BACKEND_CORS_ORIGINS:
        origin_str = str(origin).rstrip('/')
        origins.append(origin_str)
        origins.append(f"{origin_str}/")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

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
            # Check if outreach_messages table exists
            result = await db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'outreach_messages'
                );
            """))
            
            if not result.scalar():
                print("outreach_messages table not found - creating tables...")
                
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
    return {
        "message": "Welcome to Promtitude API",
        "version": settings.VERSION,
        "docs": "/docs",
    }


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
            
            if 'outreach_messages' not in existing_tables:
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
                
                # Create indexes
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_messages_user_id ON outreach_messages(user_id)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_messages_resume_id ON outreach_messages(resume_id)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_messages_status ON outreach_messages(status)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_messages_created_at ON outreach_messages(created_at)"))
                
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