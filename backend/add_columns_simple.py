#!/usr/bin/env python3
"""Add LinkedIn columns using psycopg2."""

import os
import psycopg2
from urllib.parse import urlparse

# Get DATABASE_URL from environment
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print("❌ DATABASE_URL not found in environment")
    exit(1)

# Parse the URL
url = urlparse(database_url)

print(f"📊 Connecting to database at {url.hostname}...")

# Connect using psycopg2
try:
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    
    print("🔨 Adding LinkedIn columns...")
    
    # Add columns
    try:
        cur.execute("""
            ALTER TABLE resumes 
            ADD COLUMN linkedin_url VARCHAR UNIQUE,
            ADD COLUMN linkedin_data JSON,
            ADD COLUMN last_linkedin_sync TIMESTAMP WITH TIME ZONE
        """)
        conn.commit()
        print("✅ LinkedIn columns added!")
    except psycopg2.errors.DuplicateColumn:
        print("ℹ️  Some columns already exist, that's okay!")
        conn.rollback()
        
        # Try adding them one by one
        for column, dtype in [
            ('linkedin_url', 'VARCHAR UNIQUE'),
            ('linkedin_data', 'JSON'),
            ('last_linkedin_sync', 'TIMESTAMP WITH TIME ZONE')
        ]:
            try:
                cur.execute(f"ALTER TABLE resumes ADD COLUMN {column} {dtype}")
                conn.commit()
                print(f"✅ Added column: {column}")
            except psycopg2.errors.DuplicateColumn:
                print(f"ℹ️  Column {column} already exists")
                conn.rollback()
    
    # Create index
    try:
        cur.execute("CREATE INDEX ix_resumes_linkedin_url ON resumes(linkedin_url)")
        conn.commit()
        print("✅ Index created!")
    except psycopg2.errors.DuplicateObject:
        print("ℹ️  Index already exists")
        conn.rollback()
    
    # Create import history table
    try:
        cur.execute("""
            CREATE TABLE linkedin_import_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id),
                resume_id UUID REFERENCES resumes(id),
                linkedin_url VARCHAR NOT NULL,
                import_status VARCHAR NOT NULL,
                error_message TEXT,
                raw_data JSON,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                source VARCHAR
            )
        """)
        conn.commit()
        print("✅ Import history table created!")
    except psycopg2.errors.DuplicateTable:
        print("ℹ️  Import history table already exists")
        conn.rollback()
    
    # Close connection
    cur.close()
    conn.close()
    
    print("\n🎉 All LinkedIn database changes completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)