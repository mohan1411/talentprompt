"""Test script to verify local database setup for pipeline feature."""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("postgres://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL


async def test_pipeline_data():
    """Test the pipeline data setup."""
    
    print("🔍 Testing Pipeline Data Setup...")
    print("=" * 60)
    
    # Create async engine
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
    
    # Create async session
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    
    async with async_session() as session:
        try:
            # 1. Check candidates table
            result = await session.execute(text("SELECT COUNT(*) FROM candidates"))
            candidate_count = result.scalar()
            print(f"✓ Candidates table: {candidate_count} records")
            
            # 2. Check resumes table
            result = await session.execute(text("SELECT COUNT(*) FROM resumes"))
            resume_count = result.scalar()
            print(f"✓ Resumes table: {resume_count} records")
            
            # 3. Check for orphaned resumes (no corresponding candidate)
            result = await session.execute(text("""
                SELECT COUNT(*) 
                FROM resumes r 
                WHERE NOT EXISTS (
                    SELECT 1 FROM candidates c WHERE c.resume_id = r.id
                )
            """))
            orphaned_resumes = result.scalar()
            print(f"⚠️ Orphaned resumes (no candidate): {orphaned_resumes}")
            
            if orphaned_resumes > 0:
                print("\n📝 Creating missing candidates...")
                await session.execute(text("""
                    INSERT INTO candidates (
                        resume_id, first_name, last_name, email, phone,
                        current_title, location, created_at, updated_at
                    )
                    SELECT 
                        id, first_name, last_name, email, phone,
                        current_title, location, created_at, updated_at
                    FROM resumes
                    WHERE NOT EXISTS (
                        SELECT 1 FROM candidates c WHERE c.resume_id = resumes.id
                    )
                """))
                await session.commit()
                print("✅ Missing candidates created!")
            
            # 4. Check pipeline_states table structure
            result = await session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'candidate_pipeline_states'
                AND column_name IN ('current_stage', 'metadata', 'tags', 'stage_entered_at')
                ORDER BY column_name
            """))
            columns = result.fetchall()
            print("\n📋 Pipeline States Columns:")
            for col_name, col_type in columns:
                print(f"  - {col_name}: {col_type}")
            
            # 5. Check foreign key constraints
            result = await session.execute(text("""
                SELECT 
                    tc.constraint_name,
                    ccu.table_name AS foreign_table_name
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = 'candidate_pipeline_states'
                AND kcu.column_name = 'candidate_id'
            """))
            fk_info = result.fetchone()
            if fk_info:
                print(f"\n🔗 Foreign Key: candidate_id -> {fk_info[1]}")
                if fk_info[1] != 'candidates':
                    print("❌ ERROR: Foreign key points to wrong table!")
                    print("   Should point to 'candidates', not", fk_info[1])
            else:
                print("\n❌ No foreign key constraint found for candidate_id")
            
            # 6. Test adding a sample candidate to pipeline
            print("\n🧪 Testing pipeline addition...")
            
            # Get first resume
            result = await session.execute(text("""
                SELECT r.id, r.first_name, r.last_name, c.id as candidate_id
                FROM resumes r
                LEFT JOIN candidates c ON c.resume_id = r.id
                LIMIT 1
            """))
            test_data = result.fetchone()
            
            if test_data:
                resume_id, first_name, last_name, candidate_id = test_data
                print(f"  Resume: {first_name} {last_name} (ID: {resume_id})")
                print(f"  Candidate ID: {candidate_id}")
                
                if not candidate_id:
                    print("  ❌ No candidate record exists for this resume!")
                else:
                    print("  ✅ Candidate record exists")
            
            print("\n" + "=" * 60)
            print("✅ Test complete!")
            
        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_pipeline_data())