#!/usr/bin/env python3
"""Check the actual schema of resumes table."""

import psycopg2

print("Checking resumes table schema...")

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="promtitude",
    user="promtitude",
    password="promtitude123"
)
cur = conn.cursor()

# Get column information
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'resumes'
    ORDER BY ordinal_position
""")

print("\nResumes table columns:")
for col_name, data_type, nullable in cur.fetchall():
    print(f"  - {col_name}: {data_type} {'(nullable)' if nullable == 'YES' else '(required)'}")

cur.close()
conn.close()