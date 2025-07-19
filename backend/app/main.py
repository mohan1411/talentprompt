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
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        print("Running in Railway environment - initializing database...")
        try:
            from app.core.init_db import init_db
            result = await init_db()
            print(f"Database initialization complete: {result}")
        except Exception as e:
            print(f"Warning: Database initialization failed: {e}")
            # Don't fail startup, let the app continue
    else:
        print("Not in Railway environment - skipping auto database init")


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
    import subprocess
    import psycopg2
    from urllib.parse import urlparse
    
    results = {
        "status": "starting",
        "alembic_migration": None,
        "direct_sql": None,
        "tables_check": None
    }
    
    # Try alembic migrations first
    try:
        result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
        if result.returncode == 0:
            results["alembic_migration"] = "success"
            results["status"] = "completed"
        else:
            results["alembic_migration"] = f"failed: {result.stderr}"
    except Exception as e:
        results["alembic_migration"] = f"error: {str(e)}"
    
    # If alembic fails, try direct SQL
    if results["alembic_migration"] != "success":
        try:
            db_url = os.environ.get("DATABASE_URL", "")
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            
            parsed = urlparse(db_url)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port,
                database=parsed.path[1:],
                user=parsed.username,
                password=parsed.password
            )
            
            with conn.cursor() as cur:
                # Read and execute SQL file
                with open("create_outreach_tables.sql", "r") as f:
                    sql = f.read()
                cur.execute(sql)
                conn.commit()
                results["direct_sql"] = "success"
                results["status"] = "completed"
            
            conn.close()
        except Exception as e:
            results["direct_sql"] = f"error: {str(e)}"
            results["status"] = "failed"
    
    # Check if tables exist
    try:
        from app.api.v1.dependencies.database import get_db
        from sqlalchemy import text
        
        async for db in get_db():
            # Check for outreach_messages table
            result = await db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'outreach_messages'
                );
            """))
            table_exists = result.scalar()
            results["tables_check"] = {
                "outreach_messages": table_exists,
                "outreach_templates": None
            }
            
            # Check for outreach_templates table
            result = await db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'outreach_templates'
                );
            """))
            results["tables_check"]["outreach_templates"] = result.scalar()
            break
    except Exception as e:
        results["tables_check"] = f"error: {str(e)}"
    
    return results