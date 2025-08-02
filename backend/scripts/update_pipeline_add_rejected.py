#!/usr/bin/env python3
"""
Script to add 'rejected' and 'withdrawn' stages to existing pipelines
"""

import asyncio
import os
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:admin123@localhost/talentprompt')

async def update_pipeline():
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        # Get current pipeline
        result = await conn.execute(
            text('SELECT id, name, stages FROM pipelines WHERE is_default = true LIMIT 1')
        )
        pipeline = result.fetchone()
        
        if not pipeline:
            print("No default pipeline found!")
            return
            
        print(f"Found pipeline: {pipeline.name}")
        
        # Parse current stages
        current_stages = json.loads(pipeline.stages) if isinstance(pipeline.stages, str) else pipeline.stages
        print(f"Current stages: {len(current_stages)}")
        
        # Check if rejected/withdrawn already exist
        stage_ids = [stage['id'] for stage in current_stages]
        
        if 'rejected' in stage_ids and 'withdrawn' in stage_ids:
            print("Rejected and withdrawn stages already exist!")
            return
            
        # Add missing stages
        new_stages = current_stages.copy()
        
        if 'rejected' not in stage_ids:
            new_stages.append({
                "id": "rejected",
                "name": "Rejected",
                "order": 6,
                "color": "#ef4444",
                "type": "final",
                "actions": []
            })
            print("Added 'rejected' stage")
            
        if 'withdrawn' not in stage_ids:
            new_stages.append({
                "id": "withdrawn",
                "name": "Withdrawn",
                "order": 7,
                "color": "#6b7280",
                "type": "final",
                "actions": []
            })
            print("Added 'withdrawn' stage")
        
        # Update pipeline
        await conn.execute(
            text("""
                UPDATE pipelines 
                SET stages = :stages,
                    updated_at = NOW()
                WHERE id = :id
            """),
            {"stages": json.dumps(new_stages), "id": pipeline.id}
        )
        
        print(f"Pipeline updated successfully! Now has {len(new_stages)} stages")
        
        # Verify update
        result = await conn.execute(
            text('SELECT stages FROM pipelines WHERE id = :id'),
            {"id": pipeline.id}
        )
        updated = result.fetchone()
        updated_stages = json.loads(updated.stages) if isinstance(updated.stages, str) else updated.stages
        
        print("\nUpdated stages:")
        for stage in updated_stages:
            print(f"  - {stage['id']}: {stage['name']} (order: {stage['order']}, color: {stage['color']})")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(update_pipeline())