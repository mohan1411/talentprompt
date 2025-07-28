#!/usr/bin/env python3
"""Simple script to fix search indexes - uses psycopg2 directly."""

import os
import psycopg2
from urllib.parse import urlparse

print("="*60)
print("FIXING SEARCH INDEXES")
print("="*60)

# Get database URL from environment or prompt
database_url = os.getenv("DATABASE_URL")
database_url = "postgresql://postgres:jLtKYrHkYlXjWNrlVYPuDfaDznlvvSGH@gondola.proxy.rlwy.net:40203/railway"
if not database_url:
    print("\nPlease provide your Railway database URL.")
    print("You can find it in Railway dashboard > Your Service > Variables > DATABASE_URL")
    database_url = input("\nEnter DATABASE_URL: ").strip()

if not database_url:
    print("❌ No database URL provided")
    exit(1)

# Parse the URL
parsed = urlparse(database_url)

try:
    # Connect to database
    print("\nConnecting to database...")
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password,
        sslmode='require'  # Railway requires SSL
    )
    cur = conn.cursor()
    print("✅ Connected successfully")
    
    # Drop problematic indexes
    print("\n1. Dropping problematic indexes...")
    problematic_indexes = [
        'idx_resumes_full_text_gin',
        'idx_resumes_skills_text_gin',
        'idx_resumes_skills_text_trgm',
        'idx_resumes_user_skills'
    ]
    
    for idx in problematic_indexes:
        try:
            cur.execute(f"DROP INDEX IF EXISTS {idx}")
            print(f"   ✓ Dropped {idx}")
        except Exception as e:
            print(f"   - Skipped {idx}: {str(e)}")
    
    # Create pg_trgm extension
    print("\n2. Creating pg_trgm extension...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    print("   ✅ pg_trgm extension ready")
    
    # Create correct indexes
    print("\n3. Creating correct indexes...")
    
    # GIN index on raw_text
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_resumes_raw_text_gin 
        ON resumes USING GIN (to_tsvector('english', COALESCE(raw_text, '')))
    """)
    print("   ✅ Created raw_text GIN index")
    
    # GIN index on skills JSON
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_resumes_skills_gin 
        ON resumes USING GIN (to_tsvector('english', COALESCE(skills::text, '')))
    """)
    print("   ✅ Created skills GIN index")
    
    # Trigram index on skills
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_resumes_skills_trgm 
        ON resumes USING GIN ((skills::text) gin_trgm_ops)
    """)
    print("   ✅ Created skills trigram index")
    
    # Composite search index
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_resumes_composite_search_gin 
        ON resumes USING GIN (
            to_tsvector('english', 
                COALESCE(raw_text, '') || ' ' || 
                COALESCE(summary, '') || ' ' || 
                COALESCE(skills::text, '') || ' ' ||
                COALESCE(current_title, '')
            )
        )
    """)
    print("   ✅ Created composite search index")
    
    # User indexes
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_resumes_user_id 
        ON resumes (user_id)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_resumes_user_status 
        ON resumes (user_id, status)
    """)
    print("   ✅ Created user filtering indexes")
    
    # Commit changes
    conn.commit()
    print("\n✅ All indexes created successfully!")
    
    # Verify
    print("\n4. Verifying indexes...")
    cur.execute("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename = 'resumes' 
        AND (indexname LIKE '%gin%' OR indexname LIKE '%trgm%')
        ORDER BY indexname
    """)
    
    indexes = cur.fetchall()
    print(f"\nFound {len(indexes)} search indexes:")
    for idx in indexes:
        print(f"   - {idx[0]}")
    
    cur.close()
    conn.close()
    
    print("\n✅ Search indexes fixed successfully!")
    print("\nYour search should now work correctly.")
    
except psycopg2.OperationalError as e:
    print(f"\n❌ Connection error: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Make sure you're using the correct DATABASE_URL from Railway")
    print("2. Check if your database is running in Railway dashboard")
    print("3. Try running this script from within Railway shell:")
    print("   railway shell")
    print("   python backend/scripts/fix_search_indexes_simple.py")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()