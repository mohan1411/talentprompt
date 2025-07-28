#!/usr/bin/env python3
"""Check if PostgreSQL full-text search indexes exist in production."""

import psycopg2
import os
from urllib.parse import urlparse

def check_indexes():
    """Check if all required indexes exist in the database."""
    
    # Parse database URL
    db_url = input("Enter your production DATABASE_URL: ").strip()
    if not db_url:
        print("❌ No database URL provided")
        return
    
    parsed = urlparse(db_url)
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
        cur = conn.cursor()
        
        print("="*60)
        print("CHECKING PRODUCTION INDEXES")
        print("="*60)
        
        # Check for indexes
        print("\n1. Checking for full-text search indexes...")
        cur.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = 'resumes'
            AND (
                indexname LIKE '%gin%'
                OR indexname LIKE '%trgm%'
                OR indexname LIKE '%fulltext%'
                OR indexname LIKE '%search%'
            )
            ORDER BY indexname;
        """)
        
        indexes = cur.fetchall()
        if indexes:
            print(f"\n   Found {len(indexes)} search-related indexes:")
            for schema, table, name, definition in indexes:
                print(f"   - {name}")
                if 'gin' in definition.lower():
                    print("     ✅ GIN index (good for full-text search)")
                if 'trgm' in definition.lower():
                    print("     ✅ Trigram index (good for fuzzy matching)")
        else:
            print("   ❌ No full-text search indexes found!")
        
        # Check for pg_trgm extension
        print("\n2. Checking for pg_trgm extension...")
        cur.execute("""
            SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm';
        """)
        
        if cur.fetchone():
            print("   ✅ pg_trgm extension is installed")
        else:
            print("   ❌ pg_trgm extension is NOT installed")
        
        # Check for required columns
        print("\n3. Checking for required columns...")
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'resumes'
            AND column_name IN ('full_text', 'skills_text', 'raw_text')
            ORDER BY column_name;
        """)
        
        columns = cur.fetchall()
        print(f"\n   Found {len(columns)} text columns:")
        for col_name, data_type in columns:
            print(f"   - {col_name}: {data_type}")
        
        # Check Alembic version
        print("\n4. Checking Alembic migrations...")
        cur.execute("""
            SELECT version_num 
            FROM alembic_version 
            ORDER BY version_num DESC 
            LIMIT 5;
        """)
        
        versions = cur.fetchall()
        if versions:
            print("   Recent migrations:")
            for version in versions:
                print(f"   - {version[0]}")
                if 'fulltext' in version[0]:
                    print("     ✅ Full-text search migration found!")
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        required_indexes = [
            'idx_resumes_full_text_gin',
            'idx_resumes_skills_text_gin',
            'idx_resumes_skills_text_trgm'
        ]
        
        existing_indexes = [idx[2] for idx in indexes]
        missing_indexes = [idx for idx in required_indexes if idx not in existing_indexes]
        
        if missing_indexes:
            print(f"\n⚠️  Missing indexes: {', '.join(missing_indexes)}")
            print("\nTo create missing indexes, run the migration:")
            print("railway run alembic upgrade head")
        else:
            print("\n✅ All required indexes exist!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    check_indexes()