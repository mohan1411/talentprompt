#!/usr/bin/env python3
"""Add LinkedIn columns to the database."""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine

async def add_columns():
    # Get DATABASE_URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return
        
    # Fix the URL for asyncpg
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+asyncpg://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    print(f"📊 Connecting to database...")
    
    engine = create_async_engine(database_url)
    
    async with engine.begin() as conn:
        print("🔨 Adding LinkedIn columns...")
        
        # Add all columns in one command
        await conn.execute("""
            ALTER TABLE resumes 
            ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR UNIQUE,
            ADD COLUMN IF NOT EXISTS linkedin_data JSON,
            ADD COLUMN IF NOT EXISTS last_linkedin_sync TIMESTAMP WITH TIME ZONE
        """)
        print("✅ LinkedIn columns added!")
        
        # Create index
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_resumes_linkedin_url ON resumes(linkedin_url)
        """)
        print("✅ Index created!")
        
        # Create the import history table too
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS linkedin_import_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id),
                resume_id UUID REFERENCES resumes(id),
                linkedin_url VARCHAR NOT NULL,
                import_status VARCHAR NOT NULL,
                error_message TEXT,
                raw_data JSON,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                source VARCHAR
            )
        """)
        print("✅ Import history table created!")
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_linkedin_import_history_user_id 
            ON linkedin_import_history(user_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_linkedin_import_history_created_at 
            ON linkedin_import_history(created_at)
        """)
        print("✅ Indexes for import history created!")
    
    await engine.dispose()
    print("\n🎉 All LinkedIn database changes completed successfully!")

if __name__ == "__main__":
    asyncio.run(add_columns())