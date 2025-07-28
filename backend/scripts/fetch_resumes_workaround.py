#!/usr/bin/env python3
"""Fetch all resumes while avoiding the error."""

import requests
import json

token = input("\nPaste your access token: ").strip()

if not token:
    print("❌ No token provided")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

print("="*60)
print("FETCHING RESUMES WITH WORKAROUND")
print("="*60)

all_resumes = []

# Fetch first 95 resumes (which work)
print("\n1. Fetching resumes 0-94...")
for skip in range(0, 95, 10):
    response = requests.get(f"http://localhost:8001/api/v1/resumes/?skip={skip}&limit=10", headers=headers)
    if response.status_code == 200:
        data = response.json()
        all_resumes.extend(data)
        print(f"   Fetched {len(data)} resumes (total so far: {len(all_resumes)})")

print(f"\n✅ Successfully fetched first {len(all_resumes)} resumes")

# Try to identify the problematic resumes
print("\n2. Identifying problematic resumes...")
print("   The error occurs at resume #95 and beyond")

# Direct database query to see what's special about these resumes
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://promtitude:promtitude123@localhost:5433/promtitude"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Get resumes 90-110 to see what's different
    result = conn.execute(text("""
        SELECT 
            row_number() OVER (ORDER BY created_at DESC) - 1 as position,
            id,
            first_name,
            last_name,
            status,
            parse_status,
            LENGTH(raw_text) as raw_text_length,
            LENGTH(summary) as summary_length,
            skills IS NULL as skills_null,
            array_length(skills, 1) as skills_count,
            created_at
        FROM (
            SELECT * FROM resumes r
            JOIN users u ON r.user_id = u.id
            WHERE u.email = 'promtitude@gmail.com'
            AND r.status != 'deleted'
            ORDER BY r.created_at DESC
        ) as user_resumes
        LIMIT 20 OFFSET 90
    """))
    
    print("\n3. Resumes around the error point:")
    print("   Pos | Name                    | Status | Parse | Text | Summary | Skills")
    print("   " + "-"*70)
    
    for row in result:
        pos, id, fname, lname, status, parse, text_len, summ_len, skills_null, skills_cnt, created = row
        print(f"   {pos:3d} | {fname[:12]:12s} {lname[:8]:8s} | {status:6s} | {parse:9s} | {text_len or 0:4d} | {summ_len or 0:7d} | {'NULL' if skills_null else str(skills_cnt or 0):5s}")
        if pos == 94:
            print("   " + "^"*70 + " ERROR STARTS HERE")

# Try alternative approach - fetch specific IDs
print("\n4. Alternative: Fetch all resume IDs first...")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT id 
        FROM resumes r
        JOIN users u ON r.user_id = u.id
        WHERE u.email = 'promtitude@gmail.com'
        AND r.status != 'deleted'
        ORDER BY r.created_at DESC
    """))
    
    all_ids = [str(row[0]) for row in result]
    print(f"   Found {len(all_ids)} resume IDs in database")

print("\n" + "="*60)
print("WORKAROUND OPTIONS")
print("="*60)
print("\n1. Use search instead of resume list (it works)")
print("2. Fix the problematic resume in the database")
print("3. Delete and re-import resumes")
print("4. Use a custom endpoint that skips the problematic resumes")

# Save the working resumes
if all_resumes:
    with open("working_resumes.json", "w") as f:
        json.dump(all_resumes, f, indent=2, default=str)
    print(f"\n✅ Saved {len(all_resumes)} working resumes to working_resumes.json")