#!/usr/bin/env python3
"""
Check the enum values in the database.
Usage: DATABASE_URL=your_db_url python check_enums.py
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_enums():
    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return
    
    # Convert to async URL if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    print(f"Connecting to database...")
    
    try:
        engine = create_async_engine(database_url, echo=False)
        
        async with engine.connect() as conn:
            print("\n=== Checking Database Enums ===\n")
            
            # Check interviewstatus enum
            result = await conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'interviewstatus')
                ORDER BY enumsortorder;
            """))
            
            print("interviewstatus enum values:")
            for row in result:
                print(f"  - {row[0]}")
            
            # Check if interview mode enum exists
            result = await conn.execute(text("""
                SELECT typname 
                FROM pg_type 
                WHERE typname IN ('interviewmode', 'interview_mode')
                AND typtype = 'e';
            """))
            
            mode_enums = result.fetchall()
            if mode_enums:
                for enum_name in mode_enums:
                    print(f"\n{enum_name[0]} enum values:")
                    result = await conn.execute(text(f"""
                        SELECT enumlabel 
                        FROM pg_enum 
                        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = '{enum_name[0]}')
                        ORDER BY enumsortorder;
                    """))
                    for row in result:
                        print(f"  - {row[0]}")
            
            # Check interview_sessions table structure
            print("\n=== interview_sessions column types ===\n")
            result = await conn.execute(text("""
                SELECT column_name, data_type, udt_name 
                FROM information_schema.columns 
                WHERE table_name = 'interview_sessions'
                AND column_name IN ('status', 'interview_type', 'interview_mode', 'interview_category');
            """))
            
            for row in result:
                print(f"{row[0]}: {row[1]} ({row[2]})")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check_enums())