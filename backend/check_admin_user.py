#!/usr/bin/env python3
"""Check if admin user exists in the database."""

import asyncio
import sys
from sqlalchemy import text
from app.db.session import async_session_maker

async def check_admin_user():
    """Check if admin user exists."""
    try:
        async with async_session_maker() as db:
            # Check all users
            result = await db.execute(text("""
                SELECT email, username, is_active, is_superuser, created_at 
                FROM users 
                ORDER BY created_at
            """))
            users = result.fetchall()
            
            print(f"\nFound {len(users)} users in database:")
            print("-" * 80)
            
            for user in users:
                print(f"Email: {user[0]}")
                print(f"  Username: {user[1]}")
                print(f"  Active: {user[2]}")
                print(f"  Superuser: {user[3]}")
                print(f"  Created: {user[4]}")
                print("-" * 80)
            
            # Check specifically for admin@promtitude.com
            result = await db.execute(text("""
                SELECT email FROM users 
                WHERE email IN ('admin@promtitude.com', 'admin@example.com')
            """))
            admin_users = result.fetchall()
            
            if not admin_users:
                print("\n⚠️  No admin users found!")
                print("\nExpected admin users:")
                print("  - admin@example.com (from .env)")
                print("  - admin@promtitude.com (what you're trying)")
                print("\nTo fix this:")
                print("1. Start the backend server")
                print("2. Run: python init_db.py")
                print("3. Login with: admin@example.com / admin123")
            else:
                print("\n✅ Found admin user(s):")
                for admin in admin_users:
                    print(f"  - {admin[0]}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure:")
        print("1. Docker containers are running (docker-compose up -d)")
        print("2. Database is accessible")
        print("3. You're in the backend directory")

if __name__ == "__main__":
    print("Checking for admin user in database...")
    asyncio.run(check_admin_user())