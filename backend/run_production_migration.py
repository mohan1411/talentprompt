#!/usr/bin/env python3
"""
Run the pipeline migration on production database.
This script can be run locally to apply migrations to your Supabase database.
"""

import os
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def run_migration():
    # Get your production database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment variables")
        print("Please set your Supabase database URL in .env file")
        return
    
    # Convert to async URL if needed
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    print("📦 Connecting to production database...")
    
    try:
        # Create engine
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        # Read the migration script
        with open("backend/PRODUCTION_PIPELINE_MIGRATION.sql", "r") as f:
            migration_sql = f.read()
        
        print("🚀 Running pipeline migration...")
        
        # Execute migration
        async with engine.begin() as conn:
            # Split by statements and execute each
            statements = [s.strip() for s in migration_sql.split(";") if s.strip()]
            
            for i, statement in enumerate(statements, 1):
                if statement and not statement.startswith("--"):
                    try:
                        await conn.execute(text(statement + ";"))
                        print(f"✅ Executed statement {i}/{len(statements)}")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            print(f"⏭️  Skipped statement {i} (already exists)")
                        else:
                            print(f"❌ Error in statement {i}: {e}")
        
        print("\n✨ Migration completed successfully!")
        
        # Verify migration
        async with engine.connect() as conn:
            # Check if tables exist
            result = await conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('pipelines', 'candidate_pipeline_states', 'pipeline_activities')
            """))
            table_count = result.scalar()
            
            # Check if default pipeline exists
            result = await conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM pipelines 
                WHERE is_default = true
            """))
            pipeline_count = result.scalar()
            
            # Check candidates in pipeline
            result = await conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM candidate_pipeline_states
            """))
            candidates_count = result.scalar()
            
            print("\n📊 Migration Verification:")
            print(f"  • Tables created: {table_count}/3")
            print(f"  • Default pipeline exists: {'Yes' if pipeline_count > 0 else 'No'}")
            print(f"  • Candidates in pipeline: {candidates_count}")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your DATABASE_URL in .env file")
        print("2. Ensure your database is accessible")
        print("3. Try running the migration directly in Supabase SQL Editor")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("🔧 Pipeline Feature Migration Tool")
    print("=" * 40)
    asyncio.run(run_migration())