#!/usr/bin/env python3
"""Simple import script that only uses existing resume columns."""

import json
import os
from datetime import datetime
from uuid import uuid4
import asyncio
import asyncpg
from typing import Optional

# Configuration - Update with your actual credentials
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:promtitude123@localhost:5433/promtitude")
TEST_USER_EMAIL = "promtitude@gmail.com"
JSON_FILE = "test_resumes_100.json"


async def get_db_connection():
    """Create a database connection."""
    if DATABASE_URL.startswith("postgresql://"):
        db_url = DATABASE_URL.replace("postgresql://", "postgres://")
    else:
        db_url = DATABASE_URL
    
    try:
        conn = await asyncpg.connect(db_url)
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None


async def get_or_create_user(conn, email: str) -> Optional[str]:
    """Get or create test user."""
    # Check if user exists
    user = await conn.fetchrow(
        "SELECT id, email FROM users WHERE email = $1",
        email
    )
    
    if user:
        print(f"✓ Found existing user: {email}")
        return str(user['id'])
    
    # Create user
    user_id = str(uuid4())
    try:
        await conn.execute("""
            INSERT INTO users (id, email, full_name, is_active, is_verified, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, user_id, email, "Test User", True, True, datetime.utcnow(), datetime.utcnow())
        
        print(f"✓ Created new user: {email}")
        return user_id
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return None


async def check_table_structure(conn):
    """Check which columns exist in the resumes table."""
    print("\nChecking resumes table structure...")
    
    columns = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'resumes'
        ORDER BY ordinal_position
    """)
    
    column_names = [col['column_name'] for col in columns]
    print(f"Found {len(column_names)} columns in resumes table")
    
    # Check for important columns
    important_columns = ['id', 'user_id', 'first_name', 'last_name', 'email', 
                        'skills', 'full_text', 'skills_text', 'raw_text']
    
    for col in important_columns:
        if col in column_names:
            print(f"  ✓ {col}")
        else:
            print(f"  ✗ {col} (missing)")
    
    return column_names


async def import_resumes(conn, user_id: str, json_file: str, existing_columns: list):
    """Import resumes using only existing columns."""
    print(f"\nImporting resumes from {json_file}...")
    
    # Load JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {json_file}")
        return
    
    resumes_data = data.get('resumes', [])
    print(f"Found {len(resumes_data)} resumes to import")
    
    imported = 0
    skipped = 0
    
    for i, resume_data in enumerate(resumes_data):
        try:
            # Check if already exists
            existing = await conn.fetchrow(
                "SELECT id FROM resumes WHERE email = $1 AND user_id = $2",
                resume_data['email'], user_id
            )
            
            if existing:
                skipped += 1
                continue
            
            # Prepare data based on existing columns
            resume_id = str(uuid4())
            
            # Create full text for searching
            full_text = f"{resume_data['first_name']} {resume_data['last_name']} "
            full_text += f"{resume_data.get('current_title', '')} "
            full_text += f"{resume_data.get('summary', '')} "
            full_text += " ".join(resume_data.get('skills', []))
            
            skills_text = " ".join(resume_data.get('skills', []))
            
            # Build dynamic insert based on existing columns
            insert_columns = ['id', 'user_id', 'first_name', 'last_name', 'email']
            insert_values = [resume_id, user_id, resume_data['first_name'], 
                           resume_data['last_name'], resume_data['email']]
            
            # Add optional columns if they exist
            optional_mappings = {
                'phone': resume_data.get('phone'),
                'location': resume_data.get('location'),
                'current_title': resume_data.get('current_title'),
                'summary': resume_data.get('summary'),
                'years_experience': resume_data.get('years_experience', 0),
                'skills': json.dumps(resume_data.get('skills', [])),
                'full_text': full_text,
                'skills_text': skills_text,
                'raw_text': json.dumps(resume_data),
                'status': 'active',
                'parse_status': 'completed',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            for col, value in optional_mappings.items():
                if col in existing_columns:
                    insert_columns.append(col)
                    insert_values.append(value)
            
            # Build query
            placeholders = [f"${i+1}" for i in range(len(insert_values))]
            
            # Special handling for jsonb columns
            for i, col in enumerate(insert_columns):
                if col == 'skills' and 'skills' in existing_columns:
                    placeholders[i] = f"${i+1}::jsonb"
            
            query = f"""
                INSERT INTO resumes ({', '.join(insert_columns)})
                VALUES ({', '.join(placeholders)})
            """
            
            # Execute insert
            await conn.execute(query, *insert_values)
            
            imported += 1
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ Imported {i + 1} resumes...")
                
        except Exception as e:
            print(f"  ✗ Error importing resume {i + 1} ({resume_data.get('first_name', '')} {resume_data.get('last_name', '')}): {e}")
            continue
    
    print(f"\n✅ Import complete!")
    print(f"   - Imported: {imported}")
    print(f"   - Skipped: {skipped}")
    print(f"   - Total: {imported + skipped}")


async def verify_import(conn, user_id: str):
    """Verify the import worked."""
    count = await conn.fetchval(
        "SELECT COUNT(*) FROM resumes WHERE user_id = $1",
        user_id
    )
    
    print(f"\n📊 Verification:")
    print(f"   - Total resumes for user: {count}")
    
    # Get a few sample names
    samples = await conn.fetch("""
        SELECT first_name, last_name, current_title
        FROM resumes 
        WHERE user_id = $1 
        LIMIT 5
    """, user_id)
    
    if samples:
        print("\n   Sample resumes:")
        for s in samples:
            print(f"   - {s['first_name']} {s['last_name']} ({s['current_title']})")
    
    # Test specific searches
    print("\n   Key test cases:")
    william = await conn.fetchval(
        "SELECT COUNT(*) FROM resumes WHERE user_id = $1 AND first_name = 'William' AND last_name = 'Alves'",
        user_id
    )
    print(f"   - William Alves found: {'Yes' if william > 0 else 'No'}")
    
    # Check which text columns exist for searching
    text_columns = []
    column_info = await conn.fetch("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'resumes' 
        AND column_name IN ('skills_text', 'full_text', 'summary', 'raw_text')
    """)
    text_columns = [col['column_name'] for col in column_info]
    
    # Build search condition based on available columns
    search_conditions = []
    if 'full_text' in text_columns:
        search_conditions.append("full_text ILIKE $2")
    if 'skills_text' in text_columns:
        search_conditions.append("skills_text ILIKE $2")
    if 'summary' in text_columns:
        search_conditions.append("summary ILIKE $2")
    if 'raw_text' in text_columns:
        search_conditions.append("raw_text ILIKE $2")
    
    if search_conditions:
        search_where = f"user_id = $1 AND ({' OR '.join(search_conditions)})"
        
        python_count = await conn.fetchval(
            f"SELECT COUNT(*) FROM resumes WHERE {search_where}",
            user_id, '%python%'
        )
        print(f"   - Resumes with Python: {python_count}")
        
        aws_count = await conn.fetchval(
            f"SELECT COUNT(*) FROM resumes WHERE {search_where}",
            user_id, '%aws%'
        )
        print(f"   - Resumes with AWS: {aws_count}")
    else:
        print("   - Unable to search for Python/AWS (no text columns found)")


async def main():
    """Run the import."""
    print("="*60)
    print("TEST RESUME IMPORT (Simple Version)")
    print("="*60)
    
    # Get database connection
    conn = await get_db_connection()
    if not conn:
        return
    
    try:
        # Check table structure
        existing_columns = await check_table_structure(conn)
        
        # Get or create user
        user_id = await get_or_create_user(conn, TEST_USER_EMAIL)
        if not user_id:
            return
        
        # Import resumes
        await import_resumes(conn, user_id, JSON_FILE, existing_columns)
        
        # Verify
        await verify_import(conn, user_id)
        
        print("\n✅ Import complete! Next steps:")
        print("   1. Run vector indexing to enable vector search")
        print("   2. Test searches for:")
        print("      - 'Senior Python developer with AWS'")
        print("      - 'William Alves'")
        print("      - 'Python'")
        print("      - 'AWS'")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())