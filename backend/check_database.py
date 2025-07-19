#!/usr/bin/env python
"""Check database status and tables."""
import os
import psycopg2
from urllib.parse import urlparse


def check_database():
    """Check database connection and tables."""
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set!")
        return
    
    # Handle Railway's postgres:// URLs
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    try:
        # Parse database URL
        parsed = urlparse(db_url)
        
        # Connect to database
        print(f"Connecting to database at {parsed.hostname}...")
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
            sslmode='require'  # Railway requires SSL
        )
        print("✅ Connected successfully!")
        
        with conn.cursor() as cur:
            # Check all tables
            cur.execute("""
                SELECT table_name, 
                       pg_size_pretty(pg_total_relation_size(table_schema||'.'||table_name)) as size
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            
            print("\nExisting tables:")
            print("-" * 40)
            for table_name, size in tables:
                print(f"  {table_name:<30} {size}")
            
            # Check specific outreach tables
            print("\nOutreach tables status:")
            print("-" * 40)
            
            for table in ['outreach_messages', 'outreach_templates']:
                cur.execute(f"""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = '{table}'
                """)
                exists = cur.fetchone()[0] > 0
                
                if exists:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    print(f"  {table:<30} ✅ EXISTS ({count} rows)")
                else:
                    print(f"  {table:<30} ❌ MISSING")
            
            # Check enum types
            print("\nEnum types:")
            print("-" * 40)
            cur.execute("""
                SELECT t.typname, e.enumlabel
                FROM pg_type t 
                JOIN pg_enum e ON t.oid = e.enumtypid
                WHERE t.typname IN ('messagestyle', 'messagestatus')
                ORDER BY t.typname, e.enumsortorder;
            """)
            
            current_type = None
            for type_name, enum_value in cur.fetchall():
                if type_name != current_type:
                    current_type = type_name
                    print(f"  {type_name}:")
                print(f"    - {enum_value}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_database()