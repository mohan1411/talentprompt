#!/usr/bin/env python3
"""Quick fix to create tables directly using DATABASE_URL."""

import os
import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def create_tables():
    # Get DATABASE_URL from environment or command line
    db_url = os.getenv("DATABASE_URL")
    if not db_url and len(sys.argv) > 1:
        db_url = sys.argv[1]
    
    if not db_url:
        print("❌ ERROR: Please provide DATABASE_URL")
        print("\nUsage:")
        print("  python quick_fix_tables.py 'postgresql://user:pass@host/db'")
        print("\nOr set DATABASE_URL environment variable:")
        print("  $env:DATABASE_URL='postgresql://user:pass@host/db'")
        print("  python quick_fix_tables.py")
        return
    
    # Convert to async URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    print("🚀 Creating candidate submission tables...")
    print("-" * 50)
    
    try:
        engine = create_async_engine(db_url, echo=True)
        
        async with engine.begin() as conn:
            # Create tables with simpler approach
            await conn.execute(text("""
                -- Create candidate_submissions table
                CREATE TABLE IF NOT EXISTS candidate_submissions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    token VARCHAR(255) UNIQUE NOT NULL,
                    submission_type VARCHAR(10) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                    recruiter_id UUID NOT NULL REFERENCES users(id),
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
                );
            """))
            
            await conn.execute(text("""
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create indexes
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_candidate_submissions_token ON candidate_submissions(token);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_candidate_submissions_recruiter_id ON candidate_submissions(recruiter_id);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_candidate_submissions_email ON candidate_submissions(email);"))
            
            print("\n✅ Tables created successfully!")
            
            # Verify
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name IN ('candidate_submissions', 'invitation_campaigns')
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result]
            print("\n📋 Verified tables:")
            for table in tables:
                print(f"   ✓ {table}")
                
        await engine.dispose()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTrying alternative approach...")
        
        # Try without asyncpg
        try:
            from sqlalchemy import create_engine
            
            sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
            sync_engine = create_engine(sync_url)
            
            with sync_engine.connect() as conn:
                conn.execute(text("COMMIT"))  # End any transaction
                conn.execute(text("""
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
                    );
                """))
                conn.commit()
                print("\n✅ Table created with sync connection!")
                
        except Exception as e2:
            print(f"\n❌ Sync approach also failed: {e2}")

if __name__ == "__main__":
    asyncio.run(create_tables())