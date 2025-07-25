#!/usr/bin/env python3
"""Apply the missing interview_category migration to fix the SQL error."""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from app.core.config import settings


def check_and_apply_migration():
    """Check if interview_category column exists and apply migration if needed."""
    
    # Create database engine
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    
    print("Checking database schema...")
    
    # Check if the column exists
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'interview_sessions' 
            AND column_name = 'interview_category'
        """))
        
        column_exists = result.fetchone() is not None
        
        if column_exists:
            print("✓ Column 'interview_category' already exists")
            return
        
        print("✗ Column 'interview_category' is missing")
        
        # Check current migration version
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        current_version = result.fetchone()
        
        if current_version:
            print(f"Current migration version: {current_version[0]}")
        else:
            print("No migration version found")
    
    # Try to apply the migration using alembic
    print("\nAttempting to apply migration using alembic...")
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "add_interview_mode_fields")
        print("✓ Migration applied successfully using alembic")
    except Exception as e:
        print(f"✗ Alembic migration failed: {e}")
        
        # Fallback: Apply the SQL directly
        print("\nApplying fix directly via SQL...")
        with engine.connect() as conn:
            try:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE interview_sessions 
                    ADD COLUMN interview_category VARCHAR
                """))
                conn.commit()
                print("✓ Column added successfully")
                
                # Update alembic version
                conn.execute(text("""
                    INSERT INTO alembic_version (version_num)
                    VALUES ('add_interview_mode_fields')
                    ON CONFLICT (version_num) DO NOTHING
                """))
                conn.commit()
                print("✓ Alembic version updated")
                
            except Exception as sql_error:
                print(f"✗ SQL execution failed: {sql_error}")
                raise
    
    # Verify the fix
    print("\nVerifying the fix...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'interview_sessions' 
            AND column_name = 'interview_category'
        """))
        
        if result.fetchone():
            print("✓ Column 'interview_category' now exists!")
            print("\nThe interviews page should now load without errors.")
        else:
            print("✗ Column still doesn't exist. Please check the database manually.")


if __name__ == "__main__":
    try:
        check_and_apply_migration()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease run the SQL fix manually:")
        print("ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS interview_category VARCHAR;")
        sys.exit(1)