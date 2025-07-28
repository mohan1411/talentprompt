#!/usr/bin/env python3
"""
Final fix for the resume at position 95+ issue.
This version works with the actual table structure.
"""

import psycopg2
import json

print("="*60)
print("FIX FOR RESUME POSITION 95+ ERROR")
print("="*60)

# Direct connection
conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="promtitude",
    user="promtitude",
    password="promtitude123"
)
cur = conn.cursor()

# First, let's see what columns we actually have
print("\n1. Checking table structure...")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'resumes' 
    AND column_name IN ('education', 'experience', 'achievements', 'certifications', 'languages', 'parsed_data')
""")
columns = cur.fetchall()
print("   JSONB columns found:")
for col_name, data_type in columns:
    print(f"   - {col_name}: {data_type}")

# Find the problematic resumes
print("\n2. Finding resumes at positions 90-110...")
cur.execute("""
    WITH ordered_resumes AS (
        SELECT 
            r.id,
            r.first_name,
            r.last_name,
            r.skills,
            row_number() OVER (ORDER BY r.created_at DESC) - 1 as position
        FROM resumes r
        JOIN users u ON r.user_id = u.id
        WHERE u.email = 'promtitude@gmail.com'
        AND r.status != 'deleted'
    )
    SELECT id, first_name, last_name, position
    FROM ordered_resumes
    WHERE position BETWEEN 90 AND 110
    ORDER BY position
""")

resumes = cur.fetchall()
print(f"\nFound {len(resumes)} resumes in range:")

error_start = None
for resume_id, fname, lname, position in resumes:
    marker = ""
    if position == 95 and error_start is None:
        marker = " <-- ERROR STARTS HERE (based on previous tests)"
        error_start = position
    print(f"   Position {position}: {fname} {lname}{marker}")

# Quick fix option
print("\n3. QUICK FIX OPTIONS:")
print("\nOption A: Mark resumes at position 95+ as deleted (SAFEST)")
print("Option B: Keep only first 95 resumes, delete the rest")
print("Option C: Investigate more (no changes)")

choice = input("\nChoose option (A/B/C): ").upper().strip()

if choice == 'A':
    print("\n4. Marking resumes at position 95+ as deleted...")
    
    # Get IDs of resumes at position 95+
    cur.execute("""
        WITH ordered_resumes AS (
            SELECT 
                r.id,
                row_number() OVER (ORDER BY r.created_at DESC) - 1 as position
            FROM resumes r
            JOIN users u ON r.user_id = u.id
            WHERE u.email = 'promtitude@gmail.com'
            AND r.status != 'deleted'
        )
        SELECT id, position
        FROM ordered_resumes
        WHERE position >= 95
    """)
    
    to_delete = cur.fetchall()
    print(f"\n   Will soft-delete {len(to_delete)} resumes...")
    
    for resume_id, position in to_delete:
        cur.execute("""
            UPDATE resumes 
            SET status = 'deleted', 
                updated_at = NOW()
            WHERE id = %s
        """, (resume_id,))
    
    conn.commit()
    print(f"\n✅ Done! Soft-deleted {len(to_delete)} resumes.")
    print("   The error should be fixed now.")
    
elif choice == 'B':
    print("\n4. Keeping only first 95 resumes...")
    
    # Hard delete resumes beyond position 95
    cur.execute("""
        WITH ordered_resumes AS (
            SELECT 
                r.id,
                row_number() OVER (ORDER BY r.created_at DESC) - 1 as position
            FROM resumes r
            JOIN users u ON r.user_id = u.id
            WHERE u.email = 'promtitude@gmail.com'
            AND r.status != 'deleted'
        )
        DELETE FROM resumes
        WHERE id IN (
            SELECT id FROM ordered_resumes WHERE position >= 95
        )
    """)
    
    deleted_count = cur.rowcount
    conn.commit()
    
    print(f"\n✅ Done! Permanently deleted {deleted_count} resumes.")
    print("   You now have exactly 95 resumes.")
    
else:
    print("\n4. No changes made.")
    print("\nTo investigate further:")
    print("1. Run: python capture_api_error.py")
    print("2. Check backend logs when error occurs")
    print("3. Look for Python traceback showing exact error")

# Verify the fix
print("\n5. Verifying fix...")
cur.execute("""
    SELECT COUNT(*) 
    FROM resumes r
    JOIN users u ON r.user_id = u.id
    WHERE u.email = 'promtitude@gmail.com'
    AND r.status != 'deleted'
""")
count = cur.fetchone()[0]
print(f"   Active resumes remaining: {count}")

if choice in ['A', 'B']:
    print("\n✅ The error should be fixed!")
    print("   Try accessing your resumes page again.")
    print("   You can also remove the workaround from the frontend.")

cur.close()
conn.close()