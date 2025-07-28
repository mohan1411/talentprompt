#!/usr/bin/env python3
"""Check if resumes exist in database for user."""

import psycopg2
import os
from datetime import datetime

# Load environment
try:
    from load_env import load_env
    load_env()
except:
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:promtitude123@localhost:5433/promtitude")

print("="*60)
print("RESUME DATABASE CHECK")
print("="*60)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # First, find the user
    email = "promtitude@gmail.com"
    cur.execute("SELECT id, email, full_name FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    
    if not user:
        print(f"❌ User {email} not found!")
        # List all users
        cur.execute("SELECT email FROM users LIMIT 10")
        users = cur.fetchall()
        print("\nAvailable users:")
        for u in users:
            print(f"  - {u[0]}")
    else:
        user_id, email, full_name = user
        print(f"✅ Found user: {email}")
        print(f"   ID: {user_id}")
        print(f"   Name: {full_name}")
        
        # Now check resumes for this user
        print(f"\n📄 Checking resumes for user {user_id}...")
        
        # Count total resumes for this user
        cur.execute("SELECT COUNT(*) FROM resumes WHERE user_id = %s", (user_id,))
        count = cur.fetchone()[0]
        print(f"\nTotal resumes: {count}")
        
        if count > 0:
            # Get some sample resumes
            cur.execute("""
                SELECT id, first_name, last_name, current_title, created_at, status
                FROM resumes 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 5
            """, (user_id,))
            
            resumes = cur.fetchall()
            print("\nLatest 5 resumes:")
            for r in resumes:
                resume_id, first_name, last_name, title, created_at, status = r
                print(f"  - {first_name} {last_name} | {title} | Status: {status} | Created: {created_at}")
        
        # Check if there are any resumes at all in the database
        cur.execute("SELECT COUNT(*) FROM resumes")
        total_count = cur.fetchone()[0]
        print(f"\nTotal resumes in database (all users): {total_count}")
        
        # Check unique user IDs that have resumes
        cur.execute("SELECT DISTINCT user_id FROM resumes")
        user_ids = cur.fetchall()
        print(f"\nNumber of users with resumes: {len(user_ids)}")
        
        # If our user has no resumes but others do, show who has them
        if count == 0 and total_count > 0:
            print("\nUsers who have resumes:")
            cur.execute("""
                SELECT u.email, COUNT(r.id) as resume_count
                FROM users u
                JOIN resumes r ON u.id = r.user_id
                GROUP BY u.id, u.email
                ORDER BY resume_count DESC
                LIMIT 5
            """)
            
            user_resume_counts = cur.fetchall()
            for email, resume_count in user_resume_counts:
                print(f"  - {email}: {resume_count} resumes")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Database error: {e}")
    print("\nMake sure:")
    print("1. PostgreSQL is running")
    print("2. Database URL is correct")
    print("3. The database 'promtitude' exists")