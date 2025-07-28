#!/usr/bin/env python3
"""Simple investigation of resume position 95+ error."""

import psycopg2
import json

print("="*60)
print("INVESTIGATING RESUME POSITION 95+ ERROR")
print("="*60)

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="promtitude",
    user="promtitude",
    password="promtitude123"
)
cur = conn.cursor()

# Find resumes around position 95
print("\n1. Finding resumes at positions 90-105...")
cur.execute("""
    WITH ordered_resumes AS (
        SELECT 
            r.id,
            r.first_name,
            r.last_name,
            r.skills,
            r.parsed_data,
            LENGTH(r.raw_text) as text_len,
            LENGTH(r.summary) as summary_len,
            row_number() OVER (ORDER BY r.created_at DESC) - 1 as position
        FROM resumes r
        JOIN users u ON r.user_id = u.id
        WHERE u.email = 'promtitude@gmail.com'
        AND r.status != 'deleted'
    )
    SELECT position, id, first_name, last_name, 
           skills IS NULL as skills_null,
           array_length(skills, 1) as skills_count,
           parsed_data IS NULL as parsed_null,
           text_len, summary_len
    FROM ordered_resumes
    WHERE position BETWEEN 90 AND 105
    ORDER BY position
""")

results = cur.fetchall()

print(f"\nFound {len(results)} resumes:")
print("Pos | Name                    | Skills | Parsed | Text   | Summary")
print("-"*70)

error_boundary = None
for pos, id, fname, lname, skills_null, skills_count, parsed_null, text_len, summary_len in results:
    skills_info = "NULL" if skills_null else f"{skills_count or 0}"
    parsed_info = "NULL" if parsed_null else "OK"
    
    marker = ""
    if pos == 95 and error_boundary is None:
        marker = " <-- ERROR STARTS HERE?"
        error_boundary = pos
    
    print(f"{pos:3d} | {fname[:15]:15s} {lname[:8]:8s} | {skills_info:6s} | {parsed_info:6s} | {text_len or 0:6d} | {summary_len or 0:7d}{marker}")

# Check for specific issues
print("\n2. Checking for potential issues...")

# Check for extremely large fields
cur.execute("""
    WITH ordered_resumes AS (
        SELECT 
            r.id,
            LENGTH(r.raw_text) as text_len,
            LENGTH(r.summary) as summary_len,
            LENGTH(r.parsed_data::text) as parsed_len,
            row_number() OVER (ORDER BY r.created_at DESC) - 1 as position
        FROM resumes r
        JOIN users u ON r.user_id = u.id
        WHERE u.email = 'promtitude@gmail.com'
        AND r.status != 'deleted'
    )
    SELECT position, id, text_len, summary_len, parsed_len
    FROM ordered_resumes
    WHERE position BETWEEN 90 AND 105
    AND (text_len > 100000 OR summary_len > 50000 OR parsed_len > 100000)
    ORDER BY position
""")

large_resumes = cur.fetchall()
if large_resumes:
    print("\n   Found resumes with very large fields:")
    for pos, id, text_len, summary_len, parsed_len in large_resumes:
        print(f"   Position {pos}: text={text_len}, summary={summary_len}, parsed={parsed_len}")

# Check for invalid skills arrays
cur.execute("""
    WITH ordered_resumes AS (
        SELECT 
            r.id,
            r.skills,
            row_number() OVER (ORDER BY r.created_at DESC) - 1 as position
        FROM resumes r
        JOIN users u ON r.user_id = u.id
        WHERE u.email = 'promtitude@gmail.com'
        AND r.status != 'deleted'
    )
    SELECT position, id
    FROM ordered_resumes
    WHERE position BETWEEN 90 AND 105
    AND skills IS NOT NULL
    AND array_length(skills, 1) IS NULL
""")

invalid_skills = cur.fetchall()
if invalid_skills:
    print("\n   Found resumes with invalid skills arrays:")
    for pos, id in invalid_skills:
        print(f"   Position {pos}: Invalid skills array")

# Test the exact query the API uses
print("\n3. Testing API-like query...")
try:
    cur.execute("""
        SELECT 
            r.id,
            r.first_name,
            r.last_name,
            r.email,
            r.phone,
            r.skills,
            r.years_experience,
            r.current_title,
            r.location,
            r.summary,
            r.status,
            r.parse_status,
            r.job_position,
            r.created_at,
            r.updated_at,
            r.view_count
        FROM resumes r
        JOIN users u ON r.user_id = u.id
        WHERE u.email = 'promtitude@gmail.com'
        AND r.status != 'deleted'
        ORDER BY r.created_at DESC
        LIMIT 10 OFFSET 95
    """)
    
    api_results = cur.fetchall()
    print(f"   ✅ Query successful, returned {len(api_results)} rows")
    
    # Try to simulate JSON serialization
    for i, row in enumerate(api_results):
        try:
            resume_dict = {
                "id": str(row[0]),
                "first_name": row[1],
                "last_name": row[2],
                "email": row[3],
                "phone": row[4],
                "skills": row[5],
                "years_experience": row[6],
                "current_title": row[7],
                "location": row[8],
                "summary": row[9],
                "status": row[10],
                "parse_status": row[11],
                "job_position": row[12],
                "created_at": row[13].isoformat() if row[13] else None,
                "updated_at": row[14].isoformat() if row[14] else None,
                "view_count": row[15]
            }
            # This would fail if there's a serialization issue
            json.dumps(resume_dict)
            print(f"   ✅ Resume {i} at position {95+i} serializes OK")
        except Exception as e:
            print(f"   ❌ Resume {i} at position {95+i} fails: {e}")
            print(f"      Name: {row[1]} {row[2]}")
            print(f"      Skills type: {type(row[5])}")
            if row[5] and hasattr(row[5], '__len__'):
                print(f"      Skills length: {len(row[5])}")
                
except Exception as e:
    print(f"   ❌ Query failed: {e}")

print("\n" + "="*60)
print("RECOMMENDATIONS")
print("="*60)
print("\n1. Check your backend logs for the exact Python error")
print("2. The issue is likely in the Pydantic/FastAPI serialization layer")
print("3. Run temporary_fix_resume_95.py and choose option 'a' to fix")

cur.close()
conn.close()