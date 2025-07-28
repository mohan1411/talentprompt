#\!/usr/bin/env python3
"""Verify resume count after fix."""

import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="promtitude",
    user="promtitude",
    password="promtitude123"
)
cur = conn.cursor()

print("="*60)
print("RESUME COUNT VERIFICATION")
print("="*60)

# Count active resumes
cur.execute("""
    SELECT 
        COUNT(*) FILTER (WHERE r.status \!= 'deleted') as active_count,
        COUNT(*) FILTER (WHERE r.status = 'deleted') as deleted_count,
        COUNT(*) as total_count
    FROM resumes r
    JOIN users u ON r.user_id = u.id
    WHERE u.email = 'promtitude@gmail.com'
""")

active, deleted, total = cur.fetchone()

print(f"\nFor user promtitude@gmail.com:")
print(f"✅ Active resumes: {active}")
print(f"🗑️  Deleted resumes: {deleted}")
print(f"📊 Total in database: {total}")

if active == 95:
    print("\n✅ Perfect\! You have exactly 95 active resumes as expected.")
else:
    print(f"\n⚠️  Expected 95 active resumes but found {active}")

cur.close()
conn.close()
EOF < /dev/null
