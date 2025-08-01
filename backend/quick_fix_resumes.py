#!/usr/bin/env python3
"""
Quick fix for resumes without user_id.
This is a standalone script that can be run with Railway.
"""

import asyncio
import os
from datetime import datetime
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not set!")
    exit(1)

# Convert to asyncpg format if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# For asyncpg, we need the raw postgres:// URL
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)


async def fix_orphaned_resumes():
    """Fix resumes without user_id."""
    
    print("🏥 Quick Resume Fix Tool")
    print("=" * 60)
    print(f"📅 Time: {datetime.utcnow().isoformat()}")
    print(f"🔗 Database: {ASYNC_DATABASE_URL.split('@')[1] if '@' in ASYNC_DATABASE_URL else 'local'}")
    
    # Connect to database
    conn = await asyncpg.connect(ASYNC_DATABASE_URL)
    
    try:
        # Check for resumes without user_id
        print("\n🔍 Checking for resumes without user_id...")
        
        orphaned_count = await conn.fetchval(
            "SELECT COUNT(*) FROM resumes WHERE user_id IS NULL"
        )
        
        print(f"📊 Found {orphaned_count} resumes without user_id")
        
        if orphaned_count == 0:
            print("✅ All resumes have user_id set!")
            return
        
        # Show some examples
        orphaned_resumes = await conn.fetch(
            """
            SELECT id, first_name, last_name, created_at 
            FROM resumes 
            WHERE user_id IS NULL 
            LIMIT 5
            """
        )
        
        print("\n📋 Sample orphaned resumes:")
        for resume in orphaned_resumes:
            print(f"   - {resume['id']}: {resume['first_name']} {resume['last_name']} (created: {resume['created_at']})")
        
        if orphaned_count > 5:
            print(f"   ... and {orphaned_count - 5} more")
        
        # Find a user to assign to
        print("\n🔍 Finding a user to assign orphaned resumes to...")
        
        user = await conn.fetchrow(
            """
            SELECT id, email, full_name 
            FROM users 
            WHERE is_active = true 
            ORDER BY created_at 
            LIMIT 1
            """
        )
        
        if not user:
            print("❌ No active users found in the database!")
            return
        
        print(f"📧 Will assign to user: {user['email']} ({user['full_name']}) - ID: {user['id']}")
        
        # Ask for confirmation
        response = input("\n⚠️  Do you want to assign these resumes to this user? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cancelled")
            return
        
        # Update resumes
        print(f"\n🔧 Updating {orphaned_count} resumes...")
        
        result = await conn.execute(
            """
            UPDATE resumes 
            SET user_id = $1, 
                updated_at = NOW() 
            WHERE user_id IS NULL
            """,
            user['id']
        )
        
        # Extract the number from the result string (e.g., "UPDATE 65")
        updated_count = int(result.split()[-1])
        
        print(f"✅ Successfully updated {updated_count} resumes")
        
        # Show the problematic resume if it exists
        problem_resume_id = '4772e109-7dd4-43b4-9c31-a36c0095fea2'
        problem_resume = await conn.fetchrow(
            """
            SELECT id, first_name, last_name, user_id 
            FROM resumes 
            WHERE id = $1
            """,
            problem_resume_id
        )
        
        if problem_resume:
            print(f"\n📄 Status of problematic resume {problem_resume_id}:")
            print(f"   Name: {problem_resume['first_name']} {problem_resume['last_name']}")
            print(f"   User ID: {problem_resume['user_id']}")
        
        print("\n🎉 All done! The indexing errors should now be resolved.")
        print("📝 Note: The resumes will be re-indexed automatically on next access.")
        
    finally:
        await conn.close()


async def check_database_stats():
    """Show database statistics."""
    conn = await asyncpg.connect(ASYNC_DATABASE_URL)
    
    try:
        stats = await conn.fetchrow(
            """
            SELECT 
                (SELECT COUNT(*) FROM users WHERE is_active = true) as active_users,
                (SELECT COUNT(*) FROM resumes) as total_resumes,
                (SELECT COUNT(*) FROM resumes WHERE user_id IS NULL) as orphaned_resumes,
                (SELECT COUNT(*) FROM resumes WHERE parse_status = 'pending') as pending_parse,
                (SELECT COUNT(*) FROM resumes WHERE parse_status = 'completed') as parsed_resumes
            """
        )
        
        print("\n📊 Database Statistics:")
        print(f"   Active Users: {stats['active_users']}")
        print(f"   Total Resumes: {stats['total_resumes']}")
        print(f"   Orphaned Resumes: {stats['orphaned_resumes']}")
        print(f"   Pending Parse: {stats['pending_parse']}")
        print(f"   Parsed Resumes: {stats['parsed_resumes']}")
        
    finally:
        await conn.close()


async def main():
    """Main function."""
    try:
        # Show stats first
        await check_database_stats()
        
        # Then fix orphaned resumes
        await fix_orphaned_resumes()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure you're running this with Railway environment:")
        print("   railway run python quick_fix_resumes.py")


if __name__ == "__main__":
    asyncio.run(main())