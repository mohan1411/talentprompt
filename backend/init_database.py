#!/usr/bin/env python
"""Initialize database tables for production deployment."""
import os
import sys
import psycopg2
from urllib.parse import urlparse


def init_database():
    """Initialize database with outreach tables."""
    print("Initializing database tables...")
    
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set!")
        return False
    
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
        
        with conn.cursor() as cur:
            # Check current state
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            existing_tables = [row[0] for row in cur.fetchall()]
            print(f"Existing tables: {existing_tables}")
            
            # Read and execute SQL file
            sql_file = os.path.join(os.path.dirname(__file__), "create_outreach_tables.sql")
            with open(sql_file, "r") as f:
                sql = f.read()
            
            print("Executing SQL to create tables...")
            cur.execute(sql)
            conn.commit()
            
            # Verify tables were created
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('outreach_messages', 'outreach_templates')
                ORDER BY table_name;
            """)
            created_tables = [row[0] for row in cur.fetchall()]
            print(f"Verified tables: {created_tables}")
            
            if 'outreach_messages' in created_tables and 'outreach_templates' in created_tables:
                print("✅ Database initialization successful!")
                return True
            else:
                print("❌ Some tables were not created properly")
                return False
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)