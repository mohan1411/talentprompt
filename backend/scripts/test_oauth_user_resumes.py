#!/usr/bin/env python3
"""Test if OAuth user can access their resumes."""

import asyncio
import asyncpg
import os

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:promtitude123@localhost:5433/promtitude")
TEST_USER_EMAIL = "promtitude@gmail.com"


async def check_oauth_user_resumes():
    """Check OAuth user and their resumes."""
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
    print("OAUTH USER RESUME CHECK")
    print("="*60)
    
    try:
        # Check user
        user = await conn.fetchrow("""
            SELECT id, email, full_name, is_active, created_at,
                   CASE WHEN oauth_provider IS NOT NULL THEN oauth_provider ELSE 'Not OAuth' END as provider
            FROM users 
            WHERE email = $1
        """, TEST_USER_EMAIL)
        
        if not user:
            print(f"❌ User {TEST_USER_EMAIL} not found!")
            
            # List all users
            print("\n📋 All users in database:")
            all_users = await conn.fetch("""
                SELECT email, 
                       CASE WHEN oauth_provider IS NOT NULL THEN 'OAuth' ELSE 'Regular' END as type,
                       is_active
                FROM users 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            
            for u in all_users:
                print(f"  - {u['email']} ({u['type']}) - Active: {u['is_active']}")
            
            return
        
        user_id = user['id']
        print(f"✓ Found user: {user['email']}")
        print(f"  ID: {user_id}")
        print(f"  Name: {user['full_name']}")
        print(f"  Active: {user['is_active']}")
        print(f"  Provider: {user['provider']}")
        print(f"  Created: {user['created_at']}")
        
        # Check resumes
        resume_count = await conn.fetchval(
            "SELECT COUNT(*) FROM resumes WHERE user_id = $1",
            user_id
        )
        
        print(f"\n📊 Resumes: {resume_count}")
        
        if resume_count > 0:
            # Get sample resumes
            print("\n📋 Sample resumes:")
            resumes = await conn.fetch("""
                SELECT id, first_name, last_name, email, current_title, 
                       status, parse_status, created_at
                FROM resumes 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT 5
            """, user_id)
            
            for r in resumes:
                print(f"\n  Resume: {r['first_name']} {r['last_name']}")
                print(f"    ID: {r['id']}")
                print(f"    Email: {r['email']}")
                print(f"    Status: {r['status']}")
                print(f"    Parse Status: {r['parse_status']}")
            
            # Check if resumes would be visible in API
            print("\n🔍 API visibility check:")
            active_count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM resumes 
                WHERE user_id = $1 
                AND status = 'active' 
                AND parse_status = 'completed'
            """, user_id)
            
            print(f"  Active & Parsed resumes: {active_count}")
            
            if active_count < resume_count:
                print(f"  ⚠️  Only {active_count} out of {resume_count} resumes are visible in API")
                
                # Check what's wrong
                inactive = await conn.fetchval(
                    "SELECT COUNT(*) FROM resumes WHERE user_id = $1 AND status != 'active'",
                    user_id
                )
                unparsed = await conn.fetchval(
                    "SELECT COUNT(*) FROM resumes WHERE user_id = $1 AND parse_status != 'completed'",
                    user_id
                )
                
                if inactive > 0:
                    print(f"     - {inactive} resumes have status != 'active'")
                if unparsed > 0:
                    print(f"     - {unparsed} resumes have parse_status != 'completed'")
        
        print("\n✅ Check complete!")
        
        if user['is_active'] and resume_count > 0:
            print("\n📌 Next steps:")
            print("1. Generate an access token:")
            print("   python generate_oauth_token.py")
            print("\n2. Use the token to access the API:")
            print("   - Add to localStorage in browser")
            print("   - Or use in API testing tools")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_oauth_user_resumes())