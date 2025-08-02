#!/usr/bin/env python3
"""
Run this script to add missing columns to the database.
Usage: python run_migration.py
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def run_migration():
    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Please set it to your PostgreSQL connection string")
        return
    
    # Convert to async URL if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    print(f"Connecting to database...")
    
    try:
        # Create engine
        engine = create_async_engine(database_url, echo=True)
        
        async with engine.begin() as conn:
            print("\n=== Adding missing columns to interview_sessions ===\n")
            
            # Add candidate_id column
            print("Adding candidate_id column...")
            await conn.execute(text("""
                ALTER TABLE interview_sessions 
                ADD COLUMN IF NOT EXISTS candidate_id UUID
            """))
            print("✓ candidate_id column added (or already exists)")
            
            # Add job_id column
            print("Adding job_id column...")
            await conn.execute(text("""
                ALTER TABLE interview_sessions 
                ADD COLUMN IF NOT EXISTS job_id UUID
            """))
            print("✓ job_id column added (or already exists)")
            
            print("\n=== Migration complete! ===\n")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nIf you see a connection error, please check your DATABASE_URL")

if __name__ == "__main__":
    asyncio.run(run_migration())