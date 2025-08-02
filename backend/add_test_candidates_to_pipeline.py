#!/usr/bin/env python3
"""
Add existing candidates to the default pipeline if they're not already in it.
This helps populate the pipeline with existing data.
"""

import os
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def add_candidates_to_pipeline():
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
    
    print("🚀 Adding Candidates to Pipeline")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(f"postgresql://{DATABASE_URL}")
        
        # Get default pipeline
        pipeline = await conn.fetchrow("""
            SELECT id, name FROM pipelines WHERE is_default = true
        """)
        
        if not pipeline:
            print("❌ No default pipeline found. Please run migration first.")
            return
        
        print(f"✅ Found default pipeline: {pipeline['name']}")
        pipeline_id = pipeline['id']
        
        # Get all candidates
        candidates = await conn.fetch("""
            SELECT 
                c.id,
                c.first_name,
                c.last_name,
                c.email,
                i.status as interview_status,
                i.overall_rating,
                i.recommendation
            FROM candidates c
            LEFT JOIN interview_sessions i ON i.candidate_id = c.id
            WHERE NOT EXISTS (
                SELECT 1 FROM candidate_pipeline_states cps
                WHERE cps.candidate_id = c.id
                AND cps.pipeline_id = $1
            )
        """, pipeline_id)
        
        if not candidates:
            print("\n✅ All candidates are already in the pipeline!")
            
            # Show current distribution
            distribution = await conn.fetch("""
                SELECT 
                    current_stage,
                    COUNT(*) as count
                FROM candidate_pipeline_states
                WHERE pipeline_id = $1
                GROUP BY current_stage
                ORDER BY 
                    CASE current_stage
                        WHEN 'applied' THEN 1
                        WHEN 'screening' THEN 2
                        WHEN 'interview' THEN 3
                        WHEN 'offer' THEN 4
                        WHEN 'hired' THEN 5
                        WHEN 'rejected' THEN 6
                        WHEN 'withdrawn' THEN 7
                    END
            """, pipeline_id)
            
            print("\n📊 Current Pipeline Distribution:")
            for row in distribution:
                print(f"  • {row['current_stage'].capitalize()}: {row['count']} candidates")
            
            return
        
        print(f"\n📋 Found {len(candidates)} candidates not in pipeline")
        
        # Add candidates to pipeline
        added = 0
        for candidate in candidates:
            # Determine initial stage based on interview status
            stage = 'applied'  # Default stage
            
            if candidate['interview_status']:
                if candidate['interview_status'] == 'completed':
                    if candidate['overall_rating'] and candidate['overall_rating'] >= 4:
                        stage = 'offer'
                    elif candidate['overall_rating'] and candidate['overall_rating'] <= 2:
                        stage = 'rejected'
                    elif candidate['recommendation'] == 'hire':
                        stage = 'offer'
                    elif candidate['recommendation'] == 'no_hire':
                        stage = 'rejected'
                    else:
                        stage = 'interview'
                elif candidate['interview_status'] in ['scheduled', 'in_progress']:
                    stage = 'interview'
            
            try:
                await conn.execute("""
                    INSERT INTO candidate_pipeline_states (
                        candidate_id,
                        pipeline_id,
                        current_stage,
                        stage_entered_at
                    ) VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                """, candidate['id'], pipeline_id, stage)
                
                added += 1
                print(f"  ✅ Added {candidate['first_name']} {candidate['last_name']} to '{stage}' stage")
                
                # Log activity
                state_id = await conn.fetchval("""
                    SELECT id FROM candidate_pipeline_states
                    WHERE candidate_id = $1 AND pipeline_id = $2
                """, candidate['id'], pipeline_id)
                
                await conn.execute("""
                    INSERT INTO pipeline_activities (
                        pipeline_state_id,
                        activity_type,
                        to_stage,
                        details,
                        created_at
                    ) VALUES ($1, 'moved', $2, $3, CURRENT_TIMESTAMP)
                """, state_id, stage, '{"reason": "Initial pipeline setup", "automated": true}')
                
            except Exception as e:
                print(f"  ⚠️ Failed to add {candidate['first_name']} {candidate['last_name']}: {e}")
        
        print(f"\n✨ Successfully added {added} candidates to pipeline")
        
        # Show updated distribution
        distribution = await conn.fetch("""
            SELECT 
                current_stage,
                COUNT(*) as count
            FROM candidate_pipeline_states
            WHERE pipeline_id = $1
            GROUP BY current_stage
            ORDER BY 
                CASE current_stage
                    WHEN 'applied' THEN 1
                    WHEN 'screening' THEN 2
                    WHEN 'interview' THEN 3
                    WHEN 'offer' THEN 4
                    WHEN 'hired' THEN 5
                    WHEN 'rejected' THEN 6
                    WHEN 'withdrawn' THEN 7
                END
        """, pipeline_id)
        
        print("\n📊 Updated Pipeline Distribution:")
        total = 0
        for row in distribution:
            print(f"  • {row['current_stage'].capitalize()}: {row['count']} candidates")
            total += row['count']
        print(f"  📈 Total: {total} candidates in pipeline")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(add_candidates_to_pipeline())