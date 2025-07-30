#!/usr/bin/env python3
"""Manually create candidate submission tables if Alembic fails."""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Load environment variables
load_dotenv()

# SQL to create tables
CREATE_TABLES_SQL = """
-- Create enums if they don't exist
DO $$ BEGIN
    CREATE TYPE submissiontype AS ENUM ('update', 'new');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE submissionstatus AS ENUM ('pending', 'submitted', 'processed', 'expired', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create invitation_campaigns table
CREATE TABLE IF NOT EXISTS invitation_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_type VARCHAR(50),
    source_data JSONB,
    is_public BOOLEAN DEFAULT FALSE,
    public_slug VARCHAR(100),
    email_template TEXT,
    expires_in_days INTEGER DEFAULT 7,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create candidate_submissions table
CREATE TABLE IF NOT EXISTS candidate_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(255) UNIQUE NOT NULL,
    submission_type VARCHAR(10) NOT NULL CHECK (submission_type IN ('update', 'new')),
    status VARCHAR(20) DEFAULT 'pending' NOT NULL CHECK (status IN ('pending', 'submitted', 'processed', 'expired', 'cancelled')),
    recruiter_id UUID NOT NULL REFERENCES users(id),
    campaign_id UUID REFERENCES invitation_campaigns(id),
    resume_id UUID REFERENCES resumes(id),
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    linkedin_url VARCHAR(255),
    availability VARCHAR(50),
    salary_expectations JSONB,
    location_preferences JSONB,
    resume_text TEXT,
    parsed_data JSONB,
    email_sent_at TIMESTAMP WITHOUT TIME ZONE,
    email_opened_at TIMESTAMP WITHOUT TIME ZONE,
    link_clicked_at TIMESTAMP WITHOUT TIME ZONE,
    submitted_at TIMESTAMP WITHOUT TIME ZONE,
    processed_at TIMESTAMP WITHOUT TIME ZONE,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_invitation_campaigns_recruiter_id ON invitation_campaigns(recruiter_id);
CREATE INDEX IF NOT EXISTS ix_invitation_campaigns_public_slug ON invitation_campaigns(public_slug);
CREATE INDEX IF NOT EXISTS ix_candidate_submissions_token ON candidate_submissions(token);
CREATE INDEX IF NOT EXISTS ix_candidate_submissions_recruiter_id ON candidate_submissions(recruiter_id);
CREATE INDEX IF NOT EXISTS ix_candidate_submissions_campaign_id ON candidate_submissions(campaign_id);
CREATE INDEX IF NOT EXISTS ix_candidate_submissions_email ON candidate_submissions(email);
CREATE INDEX IF NOT EXISTS ix_candidate_submissions_status ON candidate_submissions(status);

-- Update alembic version to mark this migration as complete
INSERT INTO alembic_version (version_num) 
VALUES ('add_candidate_submissions') 
ON CONFLICT (version_num) DO NOTHING;
"""

async def create_tables():
    """Create the submission tables."""
    print("🚀 Creating candidate submission tables...")
    print("-" * 50)
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable not set!")
        return False
    
    # Convert postgres:// to postgresql+asyncpg://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Mask password for display
    import re
    safe_url = re.sub(r'://[^@]+@', '://***:***@', db_url)
    print(f"📍 Database: {safe_url}")
    
    try:
        # Create engine
        engine = create_async_engine(db_url, echo=False)
        
        async with engine.begin() as conn:
            # Execute the SQL
            print("\n🔄 Creating tables...")
            await conn.execute(text(CREATE_TABLES_SQL))
            
            # Check if tables were created
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name IN ('candidate_submissions', 'invitation_campaigns')
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result]
            
            print("\n✅ Tables created successfully:")
            for table in tables:
                print(f"   - {table}")
        
        await engine.dispose()
        
        print("\n🎉 Database setup complete!")
        print("\nYou can now use the candidate submission feature.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        print("\nPossible issues:")
        print("1. Database connection failed")
        print("2. Tables might already exist")
        print("3. Permission issues")
        print("\nTry running: alembic upgrade head")
        return False

async def check_tables():
    """Check if tables exist."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return
    
    # Convert to async URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    try:
        engine = create_async_engine(db_url, echo=False)
        
        async with engine.connect() as conn:
            # Count records
            result = await conn.execute(text("""
                SELECT 
                    (SELECT COUNT(*) FROM candidate_submissions) as submissions,
                    (SELECT COUNT(*) FROM invitation_campaigns) as campaigns;
            """))
            
            row = result.first()
            if row:
                print(f"\n📊 Current data:")
                print(f"   - Submissions: {row.submissions}")
                print(f"   - Campaigns: {row.campaigns}")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"\n⚠️  Could not check table contents: {e}")

async def main():
    """Main function."""
    print("Manual Table Creation Script")
    print("=" * 50)
    
    if await create_tables():
        await check_tables()
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(main())