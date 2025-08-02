"""
Script to fix the missing candidates table in LOCAL environment only.
DO NOT RUN IN PRODUCTION - the table already exists there.
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import asyncpg
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


async def check_table_exists(session: AsyncSession, table_name: str) -> bool:
    """Check if a table exists in the database."""
    query = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = :table_name
        );
    """)
    result = await session.execute(query, {"table_name": table_name})
    return result.scalar()


async def fix_candidates_table():
    """Create candidates table and migrate data from resumes."""
    
    print("🔄 Starting local database fix for candidates table...")
    print(f"📊 Database URL: {ASYNC_DATABASE_URL[:50]}...")
    
    # Create async engine
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
    
    # Create async session
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    
    async with async_session() as session:
        try:
            # Check if candidates table exists
            candidates_exists = await check_table_exists(session, "candidates")
            print(f"✓ Candidates table exists: {candidates_exists}")
            
            # Check if resumes table exists
            resumes_exists = await check_table_exists(session, "resumes")
            print(f"✓ Resumes table exists: {resumes_exists}")
            
            if not resumes_exists:
                print("❌ Resumes table doesn't exist. Please ensure you have resumes table first.")
                return
            
            # Read and execute the SQL migration
            with open("create_candidates_table_local.sql", "r") as f:
                sql_content = f.read()
            
            # Execute the entire script as one block
            # This preserves DO $$ blocks correctly
            try:
                print(f"📝 Executing migration script...")
                await session.execute(text(sql_content))
                print("✅ Migration script executed successfully!")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"⚠️  Some objects already exist, attempting individual statements...")
                    
                    # If the full script fails, try key statements individually
                    key_statements = [
                        """CREATE TABLE IF NOT EXISTS candidates (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
                            first_name VARCHAR(100),
                            last_name VARCHAR(100),
                            email VARCHAR(255),
                            phone VARCHAR(50),
                            current_title VARCHAR(255),
                            current_company VARCHAR(255),
                            years_of_experience FLOAT,
                            skills TEXT[],
                            education JSONB,
                            experience JSONB,
                            location VARCHAR(255),
                            linkedin_url VARCHAR(500),
                            github_url VARCHAR(500),
                            portfolio_url VARCHAR(500),
                            availability VARCHAR(100),
                            salary_expectation VARCHAR(100),
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        )""",
                        
                        """INSERT INTO candidates (
                            resume_id, first_name, last_name, email, phone,
                            current_title, location, created_at, updated_at
                        )
                        SELECT 
                            id, first_name, last_name, email, phone,
                            current_title, location, created_at, updated_at
                        FROM resumes
                        WHERE NOT EXISTS (
                            SELECT 1 FROM candidates c WHERE c.resume_id = resumes.id
                        )"""
                    ]
                    
                    for stmt in key_statements:
                        try:
                            await session.execute(text(stmt))
                            print("✓ Statement executed successfully")
                        except Exception as stmt_error:
                            print(f"⚠️ Statement error: {str(stmt_error)[:100]}")
                else:
                    print(f"❌ Error in migration: {e}")
                    raise
            
            await session.commit()
            print("✅ Migration completed successfully!")
            
            # Verify the results
            result = await session.execute(text("SELECT COUNT(*) FROM candidates"))
            candidate_count = result.scalar()
            print(f"📊 Total candidates in table: {candidate_count}")
            
            result = await session.execute(text("SELECT COUNT(*) FROM resumes"))
            resume_count = result.scalar()
            print(f"📊 Total resumes in table: {resume_count}")
            
            # Check pipeline states
            result = await session.execute(text("""
                SELECT COUNT(*) FROM candidate_pipeline_states cps
                WHERE EXISTS (SELECT 1 FROM candidates c WHERE c.id = cps.candidate_id)
            """))
            valid_states = result.scalar()
            print(f"📊 Pipeline states with valid candidates: {valid_states}")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


async def quick_fix():
    """Quick fix - just create the table structure without complex migration."""
    
    print("🚀 Quick fix - Creating candidates table...")
    
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        try:
            # Simple table creation
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    email VARCHAR(255),
                    phone VARCHAR(50),
                    current_title VARCHAR(255),
                    current_company VARCHAR(255),
                    years_of_experience FLOAT,
                    skills TEXT[],
                    education JSONB,
                    experience JSONB,
                    location VARCHAR(255),
                    linkedin_url VARCHAR(500),
                    github_url VARCHAR(500),
                    portfolio_url VARCHAR(500),
                    availability VARCHAR(100),
                    salary_expectation VARCHAR(100),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.commit()
            print("✅ Candidates table created!")
            
            # First, try to add the unique constraint if it doesn't exist
            try:
                await session.execute(text("""
                    ALTER TABLE candidates 
                    ADD CONSTRAINT unique_resume_id UNIQUE (resume_id)
                """))
                print("✅ Added unique constraint on resume_id")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("✓ Unique constraint already exists")
                else:
                    print(f"⚠️ Could not add constraint: {e}")
            
            # Populate from resumes
            result = await session.execute(text("""
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
            print("✅ Candidates populated from resumes!")
            
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✓ Table already exists, skipping creation")
            else:
                print(f"❌ Error: {e}")
            await session.rollback()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════╗
    ║  LOCAL ENVIRONMENT FIX - Candidates Table  ║
    ╠════════════════════════════════════════════╣
    ║  This script will:                         ║
    ║  1. Create the candidates table            ║
    ║  2. Populate it from resumes table         ║
    ║  3. Fix pipeline state references          ║
    ╠════════════════════════════════════════════╣
    ║  ⚠️  DO NOT RUN IN PRODUCTION!             ║
    ╚════════════════════════════════════════════╝
    """)
    
    choice = input("\nChoose option:\n1. Full migration (recommended)\n2. Quick fix (simple)\nEnter choice (1 or 2): ")
    
    if choice == "1":
        asyncio.run(fix_candidates_table())
    elif choice == "2":
        asyncio.run(quick_fix())
    else:
        print("Invalid choice. Exiting.")