#!/usr/bin/env python3
"""Detailed verification of imported resumes."""

import asyncio
import asyncpg
import os
import json

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:promtitude123@localhost:5433/promtitude")
TEST_USER_EMAIL = "promtitude@gmail.com"


async def verify_resumes():
    """Verify resumes in detail."""
    if DATABASE_URL.startswith("postgresql://"):
        db_url = DATABASE_URL.replace("postgresql://", "postgres://")
    else:
        db_url = DATABASE_URL
    
    try:
        conn = await asyncpg.connect(db_url)
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return
    
    print("="*60)
    print("DETAILED RESUME VERIFICATION")
    print("="*60)
    
    try:
        # Get user
        user = await conn.fetchrow(
            "SELECT id, email FROM users WHERE email = $1",
            TEST_USER_EMAIL
        )
        
        if not user:
            print(f"❌ User {TEST_USER_EMAIL} not found")
            return
        
        user_id = user['id']
        print(f"✓ User: {TEST_USER_EMAIL}")
        print(f"  User ID: {user_id}")
        
        # Count total resumes for this user
        total_count = await conn.fetchval(
            "SELECT COUNT(*) FROM resumes WHERE user_id = $1",
            user_id
        )
        print(f"\n📊 Total resumes for this user: {total_count}")
        
        # Count ALL resumes in database
        all_count = await conn.fetchval("SELECT COUNT(*) FROM resumes")
        print(f"📊 Total resumes in database: {all_count}")
        
        # Get first 5 resumes with details
        print("\n📋 First 5 resumes:")
        resumes = await conn.fetch("""
            SELECT id, first_name, last_name, email, current_title, 
                   status, parse_status, created_at,
                   CASE WHEN skills IS NOT NULL THEN 'Yes' ELSE 'No' END as has_skills,
                   CASE WHEN raw_text IS NOT NULL AND LENGTH(raw_text) > 0 THEN 'Yes' ELSE 'No' END as has_raw_text
            FROM resumes 
            WHERE user_id = $1 
            ORDER BY created_at DESC
            LIMIT 5
        """, user_id)
        
        for r in resumes:
            print(f"\n  Resume ID: {r['id']}")
            print(f"  Name: {r['first_name']} {r['last_name']}")
            print(f"  Email: {r['email']}")
            print(f"  Title: {r['current_title']}")
            print(f"  Status: {r['status']}")
            print(f"  Parse Status: {r['parse_status']}")
            print(f"  Has Skills: {r['has_skills']}")
            print(f"  Has Raw Text: {r['has_raw_text']}")
            print(f"  Created: {r['created_at']}")
        
        # Check William Alves specifically
        print("\n🔍 Checking William Alves in detail:")
        william = await conn.fetchrow("""
            SELECT id, first_name, last_name, email, current_title, skills, user_id,
                   status, parse_status
            FROM resumes 
            WHERE first_name = 'William' AND last_name = 'Alves' AND user_id = $1
        """, user_id)
        
        if william:
            print(f"  ✓ Found William Alves")
            print(f"    ID: {william['id']}")
            print(f"    Email: {william['email']}")
            print(f"    Title: {william['current_title']}")
            print(f"    Status: {william['status']}")
            print(f"    Parse Status: {william['parse_status']}")
            if william['skills']:
                skills = json.loads(william['skills']) if isinstance(william['skills'], str) else william['skills']
                print(f"    Skills: {', '.join(skills[:5])}...")
        else:
            print("  ✗ William Alves NOT FOUND")
        
        # Check if there are any other users with resumes
        print("\n👥 Other users with resumes:")
        other_users = await conn.fetch("""
            SELECT u.email, COUNT(r.id) as resume_count
            FROM users u
            JOIN resumes r ON u.id = r.user_id
            GROUP BY u.id, u.email
            ORDER BY resume_count DESC
            LIMIT 5
        """)
        
        for u in other_users:
            print(f"  - {u['email']}: {u['resume_count']} resumes")
        
        # Check for any data issues
        print("\n⚠️  Checking for potential issues:")
        
        # Check for inactive resumes
        inactive = await conn.fetchval(
            "SELECT COUNT(*) FROM resumes WHERE user_id = $1 AND status != 'active'",
            user_id
        )
        if inactive > 0:
            print(f"  - {inactive} resumes have status != 'active'")
        
        # Check for unparsed resumes
        unparsed = await conn.fetchval(
            "SELECT COUNT(*) FROM resumes WHERE user_id = $1 AND parse_status != 'completed'",
            user_id
        )
        if unparsed > 0:
            print(f"  - {unparsed} resumes have parse_status != 'completed'")
        
        # Check if resumes are soft-deleted
        if 'deleted_at' in [col['column_name'] for col in await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'resumes'")]:
            deleted = await conn.fetchval(
                "SELECT COUNT(*) FROM resumes WHERE user_id = $1 AND deleted_at IS NOT NULL",
                user_id
            )
            if deleted > 0:
                print(f"  - {deleted} resumes are soft-deleted (deleted_at is set)")
        
        print("\n✅ Verification complete!")
        
        if total_count > 0:
            print("\n📌 The resumes ARE in the database.")
            print("   If you can't see them in the UI, check:")
            print("   1. Are you logged in as promtitude@gmail.com?")
            print("   2. Is the UI filtering by status='active'?")
            print("   3. Is the UI checking a different user_id?")
            print("   4. Try refreshing the page or clearing cache")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(verify_resumes())