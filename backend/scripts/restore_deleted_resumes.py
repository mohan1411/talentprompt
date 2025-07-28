#!/usr/bin/env python3
"""
Restore soft-deleted resumes if needed.
This can be used to undo the fix if you want to investigate further.
"""

import psycopg2
from datetime import datetime, timedelta

print("="*60)
print("RESTORE SOFT-DELETED RESUMES")
print("="*60)

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="promtitude",
    user="promtitude",
    password="promtitude123"
)
cur = conn.cursor()

# Check recently deleted resumes
print("\n1. Checking recently deleted resumes...")
cur.execute("""
    SELECT 
        COUNT(*) as total,
        MIN(updated_at) as oldest_deletion,
        MAX(updated_at) as newest_deletion
    FROM resumes r
    JOIN users u ON r.user_id = u.id
    WHERE u.email = 'promtitude@gmail.com'
    AND r.status = 'deleted'
    AND r.updated_at > NOW() - INTERVAL '1 day'
""")

total, oldest, newest = cur.fetchone()

if total == 0:
    print("   No recently deleted resumes found.")
    cur.close()
    conn.close()
    exit(0)

print(f"   Found {total} recently deleted resumes")
print(f"   Deleted between: {oldest} and {newest}")

# Show breakdown
cur.execute("""
    WITH deleted_resumes AS (
        SELECT 
            r.id,
            r.first_name,
            r.last_name,
            r.updated_at,
            row_number() OVER (ORDER BY r.updated_at DESC) as del_order
        FROM resumes r
        JOIN users u ON r.user_id = u.id
        WHERE u.email = 'promtitude@gmail.com'
        AND r.status = 'deleted'
        AND r.updated_at > NOW() - INTERVAL '1 day'
    )
    SELECT first_name, last_name, updated_at
    FROM deleted_resumes
    WHERE del_order <= 5
    ORDER BY updated_at DESC
""")

print("\n   Sample of deleted resumes:")
for fname, lname, updated in cur.fetchall():
    print(f"   - {fname} {lname} (deleted at {updated})")

# Options
print("\n2. RESTORE OPTIONS:")
print("   A: Restore all recently deleted resumes")
print("   B: Restore specific number of resumes")
print("   C: Cancel (no changes)")

choice = input("\nChoose option (A/B/C): ").upper().strip()

if choice == 'A':
    print("\n3. Restoring all recently deleted resumes...")
    
    cur.execute("""
        UPDATE resumes r
        SET status = 'active',
            updated_at = NOW()
        FROM users u
        WHERE r.user_id = u.id
        AND u.email = 'promtitude@gmail.com'
        AND r.status = 'deleted'
        AND r.updated_at > NOW() - INTERVAL '1 day'
    """)
    
    restored = cur.rowcount
    conn.commit()
    
    print(f"\n✅ Restored {restored} resumes!")
    print("   Note: The position 95+ error may return.")
    
elif choice == 'B':
    num = input("\nHow many resumes to restore? ").strip()
    try:
        num = int(num)
        
        cur.execute("""
            WITH deleted_resumes AS (
                SELECT r.id
                FROM resumes r
                JOIN users u ON r.user_id = u.id
                WHERE u.email = 'promtitude@gmail.com'
                AND r.status = 'deleted'
                AND r.updated_at > NOW() - INTERVAL '1 day'
                ORDER BY r.created_at DESC
                LIMIT %s
            )
            UPDATE resumes
            SET status = 'active',
                updated_at = NOW()
            WHERE id IN (SELECT id FROM deleted_resumes)
        """, (num,))
        
        restored = cur.rowcount
        conn.commit()
        
        print(f"\n✅ Restored {restored} resumes!")
        
    except ValueError:
        print("❌ Invalid number")
else:
    print("\nNo changes made.")

# Show final count
cur.execute("""
    SELECT COUNT(*) 
    FROM resumes r
    JOIN users u ON r.user_id = u.id
    WHERE u.email = 'promtitude@gmail.com'
    AND r.status != 'deleted'
""")
active_count = cur.fetchone()[0]

print(f"\nTotal active resumes now: {active_count}")

cur.close()
conn.close()