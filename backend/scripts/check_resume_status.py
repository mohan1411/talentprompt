#!/usr/bin/env python3
"""Check the status of imported resumes."""

import asyncio
import asyncpg
import os

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:promtitude123@localhost:5433/promtitude")
TEST_USER_EMAIL = "promtitude@gmail.com"


async def check_resumes():
    """Check resume import status."""
    # Connect to database
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
    print("RESUME IMPORT STATUS CHECK")
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
        print(f"✓ Found user: {TEST_USER_EMAIL} (ID: {user_id})")
        
        # Count resumes
        total_count = await conn.fetchval(
            "SELECT COUNT(*) FROM resumes WHERE user_id = $1",
            user_id
        )
        print(f"\n📊 Total resumes: {total_count}")
        
        if total_count == 0:
            print("❌ No resumes found for this user")
            return
        
        # Check special test cases
        print("\n🔍 Special test cases:")
        
        # William Alves
        william = await conn.fetchrow(
            "SELECT first_name, last_name, current_title FROM resumes WHERE user_id = $1 AND first_name = 'William' AND last_name = 'Alves'",
            user_id
        )
        if william:
            print(f"✓ William Alves - {william['current_title']}")
        else:
            print("✗ William Alves - NOT FOUND")
        
        # Sarah Chen
        sarah = await conn.fetchrow(
            "SELECT first_name, last_name, current_title FROM resumes WHERE user_id = $1 AND first_name = 'Sarah' AND last_name = 'Chen'",
            user_id
        )
        if sarah:
            print(f"✓ Sarah Chen - {sarah['current_title']}")
        else:
            print("✗ Sarah Chen - NOT FOUND")
        
        # Check searchable content
        print("\n📝 Checking searchable content:")
        
        # Check which columns have content
        sample = await conn.fetchrow("""
            SELECT 
                CASE WHEN full_text IS NOT NULL AND LENGTH(full_text) > 0 THEN 'Yes' ELSE 'No' END as has_full_text,
                CASE WHEN summary IS NOT NULL AND LENGTH(summary) > 0 THEN 'Yes' ELSE 'No' END as has_summary,
                CASE WHEN skills IS NOT NULL THEN 'Yes' ELSE 'No' END as has_skills,
                CASE WHEN raw_text IS NOT NULL AND LENGTH(raw_text) > 0 THEN 'Yes' ELSE 'No' END as has_raw_text
            FROM resumes 
            WHERE user_id = $1 
            LIMIT 1
        """, user_id)
        
        if sample:
            print(f"  - full_text column populated: {sample['has_full_text']}")
            print(f"  - summary column populated: {sample['has_summary']}")
            print(f"  - skills column populated: {sample['has_skills']}")
            print(f"  - raw_text column populated: {sample['has_raw_text']}")
        
        # Search for Python/AWS in available columns
        print("\n🔎 Keyword search tests:")
        
        # Try different column searches
        columns_to_search = ['full_text', 'summary', 'raw_text']
        python_found = False
        aws_found = False
        
        for col in columns_to_search:
            # Check if column exists
            col_exists = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'resumes' AND column_name = $1
            """, col)
            
            if col_exists:
                python_count = await conn.fetchval(
                    f"SELECT COUNT(*) FROM resumes WHERE user_id = $1 AND {col} ILIKE $2",
                    user_id, '%python%'
                )
                if python_count > 0:
                    python_found = True
                    print(f"  - Python found in {col}: {python_count} resumes")
                
                aws_count = await conn.fetchval(
                    f"SELECT COUNT(*) FROM resumes WHERE user_id = $1 AND {col} ILIKE $2",
                    user_id, '%aws%'
                )
                if aws_count > 0:
                    aws_found = True
                    print(f"  - AWS found in {col}: {aws_count} resumes")
        
        if not python_found:
            print("  ⚠️  Python keyword not found in any text columns")
        if not aws_found:
            print("  ⚠️  AWS keyword not found in any text columns")
        
        # Show sample resumes
        print("\n📋 Sample resumes:")
        samples = await conn.fetch("""
            SELECT first_name, last_name, current_title, years_experience
            FROM resumes 
            WHERE user_id = $1 
            ORDER BY first_name, last_name
            LIMIT 10
        """, user_id)
        
        for s in samples:
            print(f"  - {s['first_name']} {s['last_name']} - {s['current_title']} ({s['years_experience']} years)")
        
        print("\n✅ Resume data is in the database!")
        print("\n⚠️  Next steps:")
        print("1. Run vector indexing to enable Mind Reader search:")
        print("   python scripts/reindex_all_resumes.py")
        print("2. Or fix Qdrant connection issues if vector search is failing")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_resumes())