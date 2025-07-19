"""Admin endpoint to manually run migrations."""
import subprocess
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models import User

router = APIRouter()


@router.post("/run-migrations")
async def run_migrations(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> dict:
    """Manually run database migrations (superuser only)."""
    try:
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": "Migrations completed successfully",
                "output": result.stdout
            }
        else:
            return {
                "success": False,
                "message": "Migration failed",
                "error": result.stderr,
                "return_code": result.returncode
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/migration-status")
async def check_migration_status(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> dict:
    """Check current migration status."""
    try:
        # Get current revision
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True
        )
        
        # Check if outreach tables exist
        from sqlalchemy import text
        
        tables_check = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('outreach_messages', 'outreach_templates')
        """))
        
        existing_tables = [row[0] for row in tables_check]
        
        return {
            "current_revision": result.stdout.strip(),
            "outreach_tables_exist": len(existing_tables) == 2,
            "existing_tables": existing_tables,
            "alembic_output": result.stdout
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-outreach-tables")
async def create_outreach_tables(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> dict:
    """Manually create outreach tables (superuser only)."""
    try:
        from sqlalchemy import text
        
        # Read SQL file
        import os
        sql_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "create_outreach_tables.sql")
        with open(sql_path, "r") as f:
            sql = f.read()
        
        # Execute SQL
        await db.execute(text(sql))
        await db.commit()
        
        return {
            "success": True,
            "message": "Outreach tables created successfully"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))