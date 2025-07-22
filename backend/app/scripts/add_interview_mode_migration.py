"""Quick migration script to add interview mode fields."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def run_migration():
    """Add interview_category column to interview_sessions table."""
    
    # Create engine with autocommit for DDL operations
    engine = create_async_engine(
        settings.DATABASE_URL,
        isolation_level="AUTOCOMMIT"
    )
    
    async with engine.begin() as conn:
        try:
            # Check if interview_category column exists
            result = await conn.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'interview_sessions' 
                AND column_name = 'interview_category'
            """)
            
            if result.scalar() is None:
                print("Adding interview_category column...")
                await conn.execute("""
                    ALTER TABLE interview_sessions 
                    ADD COLUMN interview_category VARCHAR
                """)
                print("✓ interview_category column added successfully")
            else:
                print("✓ interview_category column already exists")
                
        except Exception as e:
            print(f"Error during migration: {e}")
            raise
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migration())