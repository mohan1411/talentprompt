"""Check database schema and identify missing columns."""

import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment!")
    exit(1)

# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

async def check_schema():
    """Check database schema for missing columns."""
    engine = create_async_engine(DATABASE_URL)
    
    print("🔍 Checking database schema...\n")
    
    # Check users table
    async with engine.connect() as conn:
        print("📋 USERS TABLE:")
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """))
        
        columns = []
        for row in result:
            columns.append(row[0])
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
        
        # Check for required columns
        required_user_columns = ['email_verification_token', 'email_verification_sent_at']
        missing_user_columns = [col for col in required_user_columns if col not in columns]
        
        if missing_user_columns:
            print(f"\n  ❌ Missing columns: {missing_user_columns}")
        else:
            print("\n  ✅ All required columns present")
    
    # Check interview_sessions table
    async with engine.connect() as conn:
        print("\n📋 INTERVIEW_SESSIONS TABLE:")
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'interview_sessions'
            ORDER BY ordinal_position
        """))
        
        columns = []
        for row in result:
            columns.append(row[0])
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
        
        # Check for required columns
        required_interview_columns = ['interviewer_id', 'transcript_data', 'recordings', 'journey_id']
        missing_interview_columns = [col for col in required_interview_columns if col not in columns]
        
        if missing_interview_columns:
            print(f"\n  ❌ Missing columns: {missing_interview_columns}")
        else:
            print("\n  ✅ All required columns present")
    
    # Check InterviewStatus enum
    async with engine.connect() as conn:
        print("\n📋 INTERVIEWSTATUS ENUM:")
        try:
            result = await conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'interviewstatus')
                ORDER BY enumsortorder
            """))
            
            values = [row[0] for row in result]
            print(f"  Values: {values}")
            
            if 'processing' not in values:
                print("  ❌ Missing 'processing' value")
            else:
                print("  ✅ All required values present")
        except Exception as e:
            print(f"  ❌ Error checking enum: {e}")
    
    await engine.dispose()
    
    print("\n" + "="*50)
    print("To fix missing columns, run:")
    print("psql -U promtitude -d promtitude -f fix_all_missing_columns.sql")
    print("Or execute the SQL in fix_all_missing_columns.sql using any PostgreSQL client")

if __name__ == "__main__":
    asyncio.run(check_schema())