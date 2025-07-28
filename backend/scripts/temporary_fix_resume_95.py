#!/usr/bin/env python3
"""
Temporary fix for the resume at position 95+ issue.

This script will:
1. Identify the problematic resumes
2. Fix any data issues
3. Or mark them as deleted to skip them
"""

import psycopg2
import json

print("="*60)
print("TEMPORARY FIX FOR RESUME POSITION 95+ ERROR")
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

# Find the problematic resumes
print("\n1. Finding resumes at positions 95-105...")
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
    WHERE position BETWEEN 95 AND 105
    ORDER BY position
""")

problematic_resumes = cur.fetchall()

print(f"\nFound {len(problematic_resumes)} resumes in the problem range:")
for resume_id, fname, lname, position in problematic_resumes:
    print(f"   Position {position}: {fname} {lname} (ID: {resume_id})")

# Check for data issues
print("\n2. Checking for data issues...")
for resume_id, fname, lname, position in problematic_resumes:
    cur.execute("""
        SELECT 
            skills IS NULL as skills_null,
            array_length(skills, 1) as skills_count,
            parsed_data IS NULL as parsed_null,
            LENGTH(raw_text) as text_len,
            LENGTH(summary) as summary_len
        FROM resumes
        WHERE id = %s
    """, (resume_id,))
    
    skills_null, skills_count, parsed_null, text_len, summary_len = cur.fetchone()
    
    issues = []
    if not skills_null and skills_count is None:
        issues.append("Invalid skills array")
    if text_len and text_len > 1000000:
        issues.append(f"Very large text ({text_len} chars)")
    if summary_len and summary_len > 100000:
        issues.append(f"Very large summary ({summary_len} chars)")
    
    if issues:
        print(f"   Position {position}: {', '.join(issues)}")
    else:
        print(f"   Position {position}: No obvious issues")

# Option to fix
print("\n3. Fix options:")
print("   a) Set problematic resumes to 'deleted' status (safest)")
print("   b) Clear potentially problematic fields")
print("   c) Do nothing (investigate more)")

choice = input("\nChoose option (a/b/c): ").lower().strip()

if choice == 'a':
    print("\nMarking problematic resumes as deleted...")
    # Only mark resumes at position 95+ as deleted
    for resume_id, fname, lname, position in problematic_resumes:
        if position >= 95:
            cur.execute("""
                UPDATE resumes 
                SET status = 'deleted', 
                    updated_at = NOW()
                WHERE id = %s
            """, (resume_id,))
            print(f"   Marked resume at position {position} as deleted")
    
    conn.commit()
    print("\n✅ Done! The error should be fixed now.")
    print("   These resumes are soft-deleted and won't appear in listings.")
    
elif choice == 'b':
    print("\nClearing potentially problematic fields...")
    for resume_id, fname, lname, position in problematic_resumes:
        if position >= 95:
            # Clear arrays that might have issues
            cur.execute("""
                UPDATE resumes 
                SET skills = CASE 
                        WHEN skills IS NOT NULL AND array_length(skills, 1) IS NULL 
                        THEN NULL 
                        ELSE skills 
                    END,
                    updated_at = NOW()
                WHERE id = %s
            """, (resume_id,))
            print(f"   Cleaned resume at position {position}")
    
    conn.commit()
    print("\n✅ Done! Try accessing the resumes again.")
    
else:
    print("\nNo changes made. You should:")
    print("1. Check the backend logs for the exact error")
    print("2. Look for serialization issues in JSONB fields")
    print("3. Check for null values in required fields")

cur.close()
conn.close()

print("\nTo verify the fix, try accessing page 2 of resumes again.")