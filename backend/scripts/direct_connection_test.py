#!/usr/bin/env python3
"""Test direct database connection and table creation."""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def test_connection(database_url):
    """Test database connection and tables."""
    print("=" * 60)
    print("DIRECT DATABASE CONNECTION TEST")
    print("=" * 60)
    
    # Parse DATABASE_URL
    parsed = urlparse(database_url)
    
    print(f"\nConnecting to:")
    print(f"  Host: {parsed.hostname}")
    print(f"  Port: {parsed.port}")
    print(f"  Database: {parsed.path[1:]}")
    print(f"  User: {parsed.username}")
    
    try:
        # Connect
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        print("\n✅ Connected successfully!")
        
        # Check current database
        cur.execute("SELECT current_database(), current_user, current_schema()")
        db_info = cur.fetchone()
        print(f"\nDatabase info:")
        print(f"  Database: {db_info[0]}")
        print(f"  User: {db_info[1]}")
        print(f"  Schema: {db_info[2]}")
        
        # Check if tables exist
        cur.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN ('candidate_submissions', 'invitation_campaigns')
            ORDER BY tablename
        """)
        
        tables = cur.fetchall()
        print(f"\nExisting tables: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        if len(tables) < 2:
            print("\n⚠️  Tables missing! Creating them now...")
            
            # Create tables
            try:
                # Drop first
                cur.execute("DROP TABLE IF EXISTS public.candidate_submissions CASCADE")
                cur.execute("DROP TABLE IF EXISTS public.invitation_campaigns CASCADE")
                
                # Create invitation_campaigns
                cur.execute("""
                    CREATE TABLE public.invitation_campaigns (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        recruiter_id UUID NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        source_type VARCHAR(50),
                        source_data JSONB,
                        is_public BOOLEAN DEFAULT FALSE,
                        public_slug VARCHAR(100),
                        email_template TEXT,
                        expires_in_days INTEGER DEFAULT 7,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create candidate_submissions
                cur.execute("""
                    CREATE TABLE public.candidate_submissions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        token VARCHAR(255) UNIQUE NOT NULL,
                        submission_type VARCHAR(10) NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                        recruiter_id UUID NOT NULL,
                        campaign_id UUID,
                        resume_id UUID,
                        email VARCHAR(255) NOT NULL,
                        first_name VARCHAR(100),
                        last_name VARCHAR(100),
                        phone VARCHAR(50),
                        linkedin_url VARCHAR(255),
                        availability VARCHAR(50),
                        salary_expectations JSONB,
                        location_preferences JSONB,
                        resume_text TEXT,
                        parsed_data JSONB,
                        email_sent_at TIMESTAMP,
                        email_opened_at TIMESTAMP,
                        link_clicked_at TIMESTAMP,
                        submitted_at TIMESTAMP,
                        processed_at TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cur.execute("CREATE INDEX ix_candidate_submissions_token ON public.candidate_submissions(token)")
                cur.execute("CREATE INDEX ix_candidate_submissions_recruiter_id ON public.candidate_submissions(recruiter_id)")
                cur.execute("CREATE INDEX ix_candidate_submissions_email ON public.candidate_submissions(email)")
                
                # Commit
                conn.commit()
                print("✅ Tables created successfully!")
                
                # Verify
                cur.execute("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename IN ('candidate_submissions', 'invitation_campaigns')
                """)
                
                verified = cur.fetchall()
                print(f"\n✅ Verified {len(verified)} tables exist:")
                for table in verified:
                    print(f"  - {table[0]}")
                    
            except Exception as e:
                print(f"\n❌ Error creating tables: {e}")
                conn.rollback()
        
        # Check all schemas
        print("\n" + "=" * 40)
        print("CHECKING ALL SCHEMAS:")
        cur.execute("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE tablename IN ('candidate_submissions', 'invitation_campaigns')
            ORDER BY schemaname, tablename
        """)
        
        all_tables = cur.fetchall()
        if all_tables:
            print(f"Found tables in these schemas:")
            for schema, table in all_tables:
                print(f"  - {schema}.{table}")
        else:
            print("❌ Tables not found in ANY schema!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Connection error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    else:
        database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("Please provide DATABASE_URL as argument or environment variable")
        print("\nUsage:")
        print("  python direct_connection_test.py 'postgresql://user:pass@host:port/database'")
        sys.exit(1)
    
    test_connection(database_url)