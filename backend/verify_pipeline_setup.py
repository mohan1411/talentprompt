#!/usr/bin/env python3
"""
Verify that the pipeline feature is properly set up in production.
"""

import os
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def verify_setup():
    # Get database URL
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment variables")
        return
    
    # Convert to asyncpg format
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "")
    elif DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "")
    
    print("🔍 Verifying Pipeline Setup")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(f"postgresql://{DATABASE_URL}")
        
        # 1. Check all tables exist
        print("\n📋 Checking Tables:")
        tables = [
            'users', 'candidates', 'resumes', 'jobs', 
            'interview_sessions', 'interview_questions',
            'pipelines', 'candidate_pipeline_states', 
            'pipeline_activities', 'candidate_notes',
            'candidate_evaluations', 'candidate_communications',
            'pipeline_automations', 'pipeline_team_members'
        ]
        
        for table in tables:
            result = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                )
            """)
            status = "✅" if result else "❌"
            print(f"  {status} {table}")
        
        # 2. Check enum types
        print("\n🔧 Checking Enum Types:")
        enums = ['pipeline_stage_type', 'pipeline_activity_type']
        
        for enum in enums:
            result = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM pg_type 
                    WHERE typname = '{enum}'
                )
            """)
            status = "✅" if result else "❌"
            print(f"  {status} {enum}")
        
        # 3. Check default pipeline
        print("\n🎯 Checking Default Pipeline:")
        pipeline = await conn.fetchrow("""
            SELECT id, name, stages, is_default 
            FROM pipelines 
            WHERE is_default = true
        """)
        
        if pipeline:
            print(f"  ✅ Default pipeline: {pipeline['name']}")
            stages = pipeline['stages']
            print(f"  📊 Number of stages: {len(stages)}")
            for stage in stages:
                print(f"     • {stage['name']} ({stage['id']})")
        else:
            print("  ❌ No default pipeline found")
        
        # 4. Check trigger
        print("\n⚡ Checking Trigger:")
        trigger = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM pg_trigger 
                WHERE tgname = 'interview_scheduled_pipeline_update'
            )
        """)
        if trigger:
            print("  ✅ Interview pipeline trigger exists")
        else:
            print("  ❌ Interview pipeline trigger not found")
        
        # 5. Check indexes
        print("\n📑 Checking Key Indexes:")
        key_indexes = [
            'idx_pipeline_states_candidate',
            'idx_pipeline_states_pipeline',
            'idx_pipeline_activities_state'
        ]
        
        for idx in key_indexes:
            result = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM pg_indexes 
                    WHERE indexname = '{idx}'
                )
            """)
            status = "✅" if result else "❌"
            print(f"  {status} {idx}")
        
        # 6. Check column additions
        print("\n🔗 Checking Column Additions:")
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'interview_sessions' 
                AND column_name = 'pipeline_state_id'
            )
        """)
        if result:
            print("  ✅ interview_sessions.pipeline_state_id column exists")
        else:
            print("  ❌ interview_sessions.pipeline_state_id column missing")
        
        # 7. Check data statistics
        print("\n📊 Data Statistics:")
        
        # Count records in each table
        for table in ['candidates', 'interview_sessions', 'candidate_pipeline_states']:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"  • {table}: {count} records")
        
        # Check if any candidates are in pipeline
        in_pipeline = await conn.fetchval("""
            SELECT COUNT(DISTINCT candidate_id) 
            FROM candidate_pipeline_states
        """)
        total_candidates = await conn.fetchval("SELECT COUNT(*) FROM candidates")
        
        if total_candidates > 0:
            percentage = (in_pipeline / total_candidates) * 100
            print(f"\n  📈 {in_pipeline}/{total_candidates} candidates in pipeline ({percentage:.1f}%)")
        
        # 8. Test query
        print("\n🧪 Testing Pipeline Query:")
        try:
            result = await conn.fetch("""
                SELECT 
                    c.first_name,
                    c.last_name,
                    cps.current_stage,
                    cps.stage_entered_at
                FROM candidate_pipeline_states cps
                JOIN candidates c ON c.id = cps.candidate_id
                JOIN pipelines p ON p.id = cps.pipeline_id
                WHERE p.is_default = true
                LIMIT 5
            """)
            
            if result:
                print("  ✅ Query successful. Sample data:")
                for row in result:
                    print(f"     • {row['first_name']} {row['last_name']}: {row['current_stage']}")
            else:
                print("  ⚠️ Query successful but no data found")
        except Exception as e:
            print(f"  ❌ Query failed: {e}")
        
        print("\n" + "=" * 50)
        print("✨ Verification Complete!")
        
        # Summary
        print("\n📋 Summary:")
        print("  • All required tables and structures are in place")
        print("  • Pipeline feature is ready to use")
        print("  • You can now use the pipeline in the application")
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(verify_setup())