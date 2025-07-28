#!/usr/bin/env python3
"""Apply full-text search indexes to production database."""

import psycopg2
from urllib.parse import urlparse

def apply_indexes():
    """Apply PostgreSQL full-text search indexes."""
    
    print("="*60)
    print("APPLYING FULL-TEXT SEARCH INDEXES")
    print("="*60)
    
    # Get database URL
    db_url = input("\nEnter your production DATABASE_URL: ").strip()
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
        
        print("\n1. Creating pg_trgm extension...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        print("   ✅ pg_trgm extension ready")
        
        print("\n2. Creating full-text search indexes...")
        
        # Check if columns exist first
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'resumes' 
            AND column_name IN ('raw_text', 'summary', 'skills', 'current_title')
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        
        indexes_created = 0
        
        # Create GIN indexes for text search
        if 'raw_text' in existing_columns:
            print("   Creating index on raw_text...")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_resumes_raw_text_gin 
                ON resumes USING GIN (to_tsvector('english', COALESCE(raw_text, '')))
            """)
            indexes_created += 1
        
        if 'summary' in existing_columns:
            print("   Creating index on summary...")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_resumes_summary_gin 
                ON resumes USING GIN (to_tsvector('english', COALESCE(summary, '')))
            """)
            indexes_created += 1
        
        # Create composite search index
        print("   Creating composite search index...")
        text_fields = []
        if 'raw_text' in existing_columns:
            text_fields.append("COALESCE(raw_text, '')")
        if 'summary' in existing_columns:
            text_fields.append("COALESCE(summary, '')")
        if 'current_title' in existing_columns:
            text_fields.append("COALESCE(current_title, '')")
        
        if text_fields:
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_resumes_composite_search_gin 
                ON resumes USING GIN (
                    to_tsvector('english', {" || ' ' || ".join(text_fields)})
                )
            """)
            indexes_created += 1
        
        # Create trigram indexes for fuzzy matching
        if 'skills' in existing_columns:
            print("   Creating trigram index on skills...")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_resumes_skills_trgm 
                ON resumes USING GIN (array_to_string(skills, ' ') gin_trgm_ops)
            """)
            indexes_created += 1
        
        if 'current_title' in existing_columns:
            print("   Creating trigram index on current_title...")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_resumes_current_title_trgm 
                ON resumes USING GIN (current_title gin_trgm_ops)
            """)
            indexes_created += 1
        
        # Create user_id index for filtering
        print("   Creating index on user_id...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_resumes_user_id 
            ON resumes (user_id)
        """)
        indexes_created += 1
        
        # Create composite index for user_id + status
        print("   Creating composite index on user_id + status...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_resumes_user_status 
            ON resumes (user_id, status)
        """)
        indexes_created += 1
        
        # Commit changes
        conn.commit()
        
        print(f"\n✅ Created {indexes_created} indexes successfully!")
        
        # Verify indexes
        print("\n3. Verifying indexes...")
        cur.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'resumes' 
            AND (indexname LIKE '%gin%' OR indexname LIKE '%trgm%')
        """)
        
        indexes = [row[0] for row in cur.fetchall()]
        print(f"   Found {len(indexes)} search indexes:")
        for idx in indexes:
            print(f"   - {idx}")
        
        cur.close()
        conn.close()
        
        print("\n✅ Full-text search indexes applied successfully!")
        print("\nThese indexes will improve:")
        print("- Keyword search performance")
        print("- Fuzzy skill matching")
        print("- Hybrid search capabilities")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure you have the correct database URL")
        print("2. Check if you have CREATE INDEX permissions")
        print("3. Some indexes might already exist (that's OK)")

if __name__ == "__main__":
    apply_indexes()