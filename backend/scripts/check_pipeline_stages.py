"""Script to check current pipeline stages in the database."""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from app.db.session import async_session_maker
from app.models import Pipeline, CandidatePipelineState


async def check_pipeline_stages():
    """Check what stages exist in the pipeline."""
    async with async_session_maker() as db:
        try:
            # Method 1: Using SQLAlchemy ORM
            print("=== Checking Pipeline Stages ===\n")
            
            result = await db.execute(
                select(Pipeline).where(Pipeline.is_default == True)
            )
            pipeline = result.scalar_one_or_none()
            
            if not pipeline:
                print("❌ No default pipeline found!")
                
                # Check if any pipelines exist
                all_pipelines = await db.execute(select(Pipeline))
                all_pipelines = all_pipelines.scalars().all()
                
                if all_pipelines:
                    print(f"\nFound {len(all_pipelines)} non-default pipeline(s):")
                    for p in all_pipelines:
                        print(f"  - {p.name} (ID: {p.id}, Default: {p.is_default})")
                        print(f"    Stages: {[s['id'] for s in p.stages]}")
                else:
                    print("❌ No pipelines exist in the database!")
                return
            
            print(f"✅ Found default pipeline: {pipeline.name}")
            print(f"   Pipeline ID: {pipeline.id}")
            print(f"   Is Active: {pipeline.is_active}")
            print(f"   Is Default: {pipeline.is_default}")
            print(f"   Number of stages: {len(pipeline.stages)}")
            
            print("\n📋 Stage Details:")
            for i, stage in enumerate(pipeline.stages, 1):
                print(f"   {i}. {stage['name']} (ID: {stage['id']})")
                print(f"      - Color: {stage['color']}")
                print(f"      - Order: {stage.get('order', 'N/A')}")
                print(f"      - Type: {stage.get('type', 'N/A')}")
            
            # Check if rejected and withdrawn exist
            stage_ids = [s['id'] for s in pipeline.stages]
            print("\n🔍 Stage Check:")
            print(f"   Has 'rejected' stage: {'✅' if 'rejected' in stage_ids else '❌'}")
            print(f"   Has 'withdrawn' stage: {'✅' if 'withdrawn' in stage_ids else '❌'}")
            
            # Method 2: Direct SQL query to double-check
            print("\n=== Direct SQL Check ===\n")
            
            result = await db.execute(
                text("""
                    SELECT 
                        id,
                        name,
                        stages::text as stages_json,
                        jsonb_array_length(stages) as stage_count
                    FROM pipelines 
                    WHERE is_default = true
                """)
            )
            row = result.fetchone()
            
            if row:
                stages_data = json.loads(row.stages_json)
                print(f"Direct SQL Result:")
                print(f"  Pipeline: {row.name}")
                print(f"  Stage count: {row.stage_count}")
                print(f"  Stage IDs from SQL: {[s['id'] for s in stages_data]}")
            
            # Check candidate distribution
            print("\n=== Candidate Distribution ===\n")
            
            result = await db.execute(
                text("""
                    SELECT 
                        current_stage_id,
                        COUNT(*) as count
                    FROM candidate_pipeline_states
                    WHERE pipeline_id = :pipeline_id
                    GROUP BY current_stage_id
                    ORDER BY current_stage_id
                """),
                {"pipeline_id": pipeline.id}
            )
            
            distribution = result.fetchall()
            if distribution:
                for stage_id, count in distribution:
                    stage_name = next((s['name'] for s in pipeline.stages if s['id'] == stage_id), stage_id)
                    print(f"  {stage_name}: {count} candidate(s)")
            else:
                print("  No candidates in pipeline")
            
            # Check for candidates that should be in rejected
            print("\n=== Candidates with Low Ratings ===\n")
            
            result = await db.execute(
                text("""
                    SELECT 
                        r.first_name,
                        r.last_name,
                        i.overall_rating,
                        cps.current_stage_id
                    FROM interview_sessions i
                    JOIN resumes r ON i.resume_id = r.id
                    LEFT JOIN candidate_pipeline_states cps ON i.pipeline_state_id = cps.id
                    WHERE i.overall_rating <= 2.0
                      AND i.status = 'completed'
                """)
            )
            
            low_rated = result.fetchall()
            if low_rated:
                print("Candidates with rating <= 2.0:")
                for first_name, last_name, rating, stage in low_rated:
                    status = "✅" if stage == "rejected" else "⚠️"
                    print(f"  {status} {first_name} {last_name}: Rating {rating}, Stage: {stage}")
            else:
                print("  No candidates with rating <= 2.0")
                
        except Exception as e:
            print(f"❌ Error checking pipeline: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_pipeline_stages())