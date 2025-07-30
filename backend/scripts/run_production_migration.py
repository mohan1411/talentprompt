#!/usr/bin/env python3
"""Run Alembic migrations on production database.

This script helps run the candidate_submissions migration on production.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Run alembic upgrade head."""
    print("🚀 Running production database migration...")
    print("-" * 50)
    
    # Check if DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable not set!")
        print("\nPlease set your production DATABASE_URL:")
        print("export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
        return False
    
    # Mask password in URL for display
    import re
    safe_url = re.sub(r'://[^@]+@', '://***:***@', db_url)
    print(f"📍 Database: {safe_url}")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    print(f"📁 Working directory: {backend_dir}")
    
    print("\n🔄 Running migration...")
    print("-" * 50)
    
    try:
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("⚠️  Errors/Warnings:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ Migration completed successfully!")
            print("\nTables created:")
            print("- candidate_submissions")
            print("- invitation_campaigns")
            return True
        else:
            print(f"\n❌ Migration failed with exit code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error running migration: {e}")
        return False

def check_tables():
    """Check if tables exist after migration."""
    print("\n🔍 Checking if tables were created...")
    
    try:
        from sqlalchemy import create_engine, text
        
        db_url = os.getenv("DATABASE_URL")
        if db_url and db_url.startswith("postgres://"):
            # Fix postgres:// to postgresql://
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Check for candidate_submissions table
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'candidate_submissions'
                );
            """))
            has_submissions = result.scalar()
            
            # Check for invitation_campaigns table
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'invitation_campaigns'
                );
            """))
            has_campaigns = result.scalar()
            
            print(f"✓ candidate_submissions table exists: {has_submissions}")
            print(f"✓ invitation_campaigns table exists: {has_campaigns}")
            
            if has_submissions and has_campaigns:
                print("\n🎉 All tables created successfully!")
                return True
            else:
                print("\n⚠️  Some tables are missing. Migration may have failed.")
                return False
                
    except Exception as e:
        print(f"\n❌ Error checking tables: {e}")
        return False

if __name__ == "__main__":
    print("Candidate Submissions Migration Script")
    print("=" * 50)
    
    # Run migration
    if run_migration():
        # Check if tables were created
        check_tables()
    
    print("\n" + "=" * 50)
    print("Migration script completed.")