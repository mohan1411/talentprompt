#!/usr/bin/env python3
import psycopg2
import json
import os

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:admin123@localhost/talentprompt')

# Convert to psycopg2 format
if DATABASE_URL.startswith('postgresql+asyncpg://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

try:
    # Get current pipeline
    cur.execute("SELECT id, name, stages FROM pipelines WHERE is_default = true LIMIT 1")
    pipeline = cur.fetchone()
    
    if not pipeline:
        print("No default pipeline found!")
    else:
        pipeline_id, name, stages = pipeline
        print(f"Found pipeline: {name}")
        
        # Parse stages
        current_stages = stages if isinstance(stages, list) else json.loads(stages)
        print(f"Current stages: {len(current_stages)}")
        
        # Check if rejected/withdrawn exist
        stage_ids = [stage['id'] for stage in current_stages]
        
        if 'rejected' not in stage_ids:
            current_stages.append({
                "id": "rejected",
                "name": "Rejected", 
                "order": 6,
                "color": "#ef4444",
                "type": "final",
                "actions": []
            })
            print("Added 'rejected' stage")
            
        if 'withdrawn' not in stage_ids:
            current_stages.append({
                "id": "withdrawn",
                "name": "Withdrawn",
                "order": 7, 
                "color": "#6b7280",
                "type": "final",
                "actions": []
            })
            print("Added 'withdrawn' stage")
            
        # Update pipeline
        cur.execute(
            "UPDATE pipelines SET stages = %s, updated_at = NOW() WHERE id = %s",
            (json.dumps(current_stages), pipeline_id)
        )
        
        conn.commit()
        print(f"Pipeline updated! Now has {len(current_stages)} stages")
        
        # Show all stages
        print("\nAll stages:")
        for stage in current_stages:
            print(f"  - {stage['id']}: {stage['name']}")
            
    # Also check if there's a candidate with rating 2.0 that needs to be moved
    cur.execute("""
        SELECT 
            r.id, r.first_name, r.last_name,
            i.overall_rating, i.recommendation,
            cps.current_stage_id
        FROM interview_sessions i
        JOIN resumes r ON i.resume_id = r.id
        LEFT JOIN candidate_pipeline_state cps ON i.pipeline_state_id = cps.id
        WHERE i.overall_rating = 2.0
          AND i.status = 'completed'
    """)
    
    candidates = cur.fetchall()
    if candidates:
        print(f"\nFound {len(candidates)} candidate(s) with rating 2.0:")
        for candidate in candidates:
            print(f"  - {candidate[1]} {candidate[2]}: Rating {candidate[3]}, Stage: {candidate[5]}")
            
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()