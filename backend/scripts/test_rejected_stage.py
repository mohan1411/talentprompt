#!/usr/bin/env python3
import asyncio
import os
import sys
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:admin123@localhost/talentprompt')

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def check_and_fix_pipeline():
    async with AsyncSessionLocal() as db:
        # Get the pipeline
        result = await db.execute(
            text("SELECT id, name, stages FROM pipelines WHERE is_default = true LIMIT 1")
        )
        pipeline = result.fetchone()
        
        if not pipeline:
            print("No default pipeline found!")
            return
            
        print(f"Found pipeline: {pipeline.name}")
        stages = json.loads(pipeline.stages) if isinstance(pipeline.stages, str) else pipeline.stages
        print(f"Current number of stages: {len(stages)}")
        
        # Check current stages
        stage_ids = [stage['id'] for stage in stages]
        print(f"Current stage IDs: {stage_ids}")
        
        # Add missing stages if needed
        updated = False
        if 'rejected' not in stage_ids:
            stages.append({
                "id": "rejected",
                "name": "Rejected",
                "order": 6,
                "color": "#ef4444",
                "type": "final",
                "actions": []
            })
            print("Added 'rejected' stage")
            updated = True
            
        if 'withdrawn' not in stage_ids:
            stages.append({
                "id": "withdrawn",
                "name": "Withdrawn",
                "order": 7,
                "color": "#6b7280",
                "type": "final",
                "actions": []
            })
            print("Added 'withdrawn' stage")
            updated = True
            
        if updated:
            # Update the pipeline
            await db.execute(
                text("""
                    UPDATE pipelines 
                    SET stages = :stages,
                        updated_at = NOW()
                    WHERE id = :id
                """),
                {"stages": json.dumps(stages), "id": pipeline.id}
            )
            await db.commit()
            print(f"Pipeline updated! Now has {len(stages)} stages")
        else:
            print("Pipeline already has rejected and withdrawn stages")
            
        # Check for candidates with rating 2.0
        result = await db.execute(
            text("""
                SELECT 
                    r.id, r.first_name, r.last_name,
                    i.overall_rating, i.recommendation,
                    cps.current_stage_id,
                    cps.id as pipeline_state_id
                FROM interview_sessions i
                JOIN resumes r ON i.resume_id = r.id
                LEFT JOIN candidate_pipeline_state cps ON i.pipeline_state_id = cps.id
                WHERE i.overall_rating <= 2.0
                  AND i.status = 'completed'
                  AND (cps.current_stage_id != 'rejected' OR cps.current_stage_id IS NULL)
            """)
        )
        
        candidates = result.fetchall()
        if candidates:
            print(f"\nFound {len(candidates)} candidate(s) with rating <= 2.0 not in rejected:")
            for candidate in candidates:
                print(f"  - {candidate.first_name} {candidate.last_name}: Rating {candidate.overall_rating}, Stage: {candidate.current_stage_id}")
                
                # Move to rejected stage
                if candidate.pipeline_state_id:
                    await db.execute(
                        text("""
                            UPDATE candidate_pipeline_state
                            SET current_stage_id = 'rejected',
                                entered_stage_at = NOW(),
                                updated_at = NOW()
                            WHERE id = :id
                        """),
                        {"id": candidate.pipeline_state_id}
                    )
                    print(f"    → Moved to rejected stage")
                    
            await db.commit()
            print("All candidates with low ratings moved to rejected stage")
        else:
            print("\nNo candidates with rating <= 2.0 found outside rejected stage")
            
        # Show final pipeline state
        print("\nFinal pipeline stages:")
        for stage in stages:
            print(f"  - {stage['id']}: {stage['name']} (color: {stage['color']})")

async def main():
    try:
        await check_and_fix_pipeline()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())