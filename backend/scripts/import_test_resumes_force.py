#!/usr/bin/env python3
"""Force import test resumes (overwrites existing ones)."""

import json
import os
from datetime import datetime, timezone
from uuid import uuid4
import asyncio
import asyncpg
from typing import Optional

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:promtitude123@localhost:5433/promtitude")
TEST_USER_EMAIL = "promtitude@gmail.com"
JSON_FILE = "test_resumes_100.json"


async def get_db_connection():
    """Create a database connection."""
    # Convert SQLAlchemy URL to asyncpg format
    db_url = DATABASE_URL
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgres://")
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgres://")
    
    try:
        conn = await asyncpg.connect(db_url)
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None


async def get_or_create_user(conn, email: str) -> Optional[str]:
    """Get or create test user."""
    user = await conn.fetchrow(
        "SELECT id, email FROM users WHERE email = $1",
        email
    )
    
    if user:
        print(f"✓ Found existing user: {email}")
        return str(user['id'])
    
    user_id = str(uuid4())
    try:
        await conn.execute("""
            INSERT INTO users (id, email, full_name, is_active, is_verified, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, user_id, email, "Test User", True, True, datetime.now(timezone.utc), datetime.now(timezone.utc))
        
        print(f"✓ Created new user: {email}")
        return user_id
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return None


async def delete_existing_resumes(conn, user_id: str):
    """Delete all existing resumes for the user."""
    print("\n🗑️  Deleting existing resumes...")
    
    count = await conn.fetchval(
        "SELECT COUNT(*) FROM resumes WHERE user_id = $1",
        user_id
    )
    
    if count > 0:
        await conn.execute(
            "DELETE FROM resumes WHERE user_id = $1",
            user_id
        )
        print(f"✓ Deleted {count} existing resumes")
    else:
        print("✓ No existing resumes to delete")


async def import_resumes(conn, user_id: str, json_file: str):
    """Import resumes from JSON file."""
    print(f"\n📥 Importing resumes from {json_file}...")
    
    # Load JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {json_file}")
        return 0
    
    resumes_data = data.get('resumes', [])
    print(f"Found {len(resumes_data)} resumes to import")
    
    # Check which columns exist
    columns = await conn.fetch("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'resumes'
    """)
    existing_columns = [col['column_name'] for col in columns]
    
    print(f"\n📋 Found {len(existing_columns)} columns in resumes table")
    print(f"   Key columns: {', '.join([c for c in existing_columns if c in ['skills', 'full_text', 'skills_text', 'raw_text']])}")
    
    imported = 0
    
    for i, resume_data in enumerate(resumes_data):
        try:
            resume_id = str(uuid4())
            
            # Create full text for searching
            full_text = f"{resume_data['first_name']} {resume_data['last_name']} "
            full_text += f"{resume_data.get('current_title', '')} "
            full_text += f"{resume_data.get('summary', '')} "
            full_text += " ".join(resume_data.get('skills', []))
            
            skills_text = " ".join(resume_data.get('skills', []))
            
            # Build insert based on existing columns
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
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
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
            
            await conn.execute(query, *insert_values)
            imported += 1
            
            if (i + 1) % 20 == 0:
                print(f"  ✓ Imported {i + 1} resumes...")
                
        except Exception as e:
            print(f"  ✗ Error importing resume {i + 1} ({resume_data.get('first_name', '')} {resume_data.get('last_name', '')})")
            print(f"     Error details: {e}")
            print(f"     Query: {query if 'query' in locals() else 'Query not built'}")
            # Continue with next resume
            continue
    
    print(f"\n✅ Import complete! Imported {imported} resumes")
    return imported


async def verify_import(conn, user_id: str):
    """Verify the import worked."""
    count = await conn.fetchval(
        "SELECT COUNT(*) FROM resumes WHERE user_id = $1",
        user_id
    )
    
    print(f"\n📊 Verification:")
    print(f"   - Total resumes for user: {count}")
    
    # Check special test cases
    special_cases = [
        ("William", "Alves"),
        ("Sarah", "Chen"),
        ("Michael", "Johnson"),
        ("Emily", "Williams"),
        ("David", "Brown")
    ]
    
    print("\n🔍 Special test cases:")
    for first, last in special_cases:
        exists = await conn.fetchval(
            "SELECT COUNT(*) FROM resumes WHERE user_id = $1 AND first_name = $2 AND last_name = $3",
            user_id, first, last
        )
        if exists:
            print(f"   ✓ {first} {last}")
        else:
            print(f"   ✗ {first} {last} - NOT FOUND")


async def main():
    """Run the force import."""
    print("="*60)
    print("FORCE IMPORT TEST RESUMES")
    print("="*60)
    
    conn = await get_db_connection()
    if not conn:
        return
    
    try:
        # Get or create user
        user_id = await get_or_create_user(conn, TEST_USER_EMAIL)
        if not user_id:
            return
        
        # Ask for confirmation
        print(f"\n⚠️  This will DELETE all existing resumes for {TEST_USER_EMAIL}")
        response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
        
        if response != 'yes':
            print("Import cancelled.")
            return
        
        # Delete existing resumes
        await delete_existing_resumes(conn, user_id)
        
        # Import new resumes
        imported = await import_resumes(conn, user_id, JSON_FILE)
        
        if imported > 0:
            # Verify
            await verify_import(conn, user_id)
            
            print("\n✅ Success! Next steps:")
            print("1. Run vector indexing: python scripts/reindex_all_resumes.py")
            print("2. Test searches:")
            print("   - 'Senior Python developer with AWS'")
            print("   - 'William Alves'")
            print("   - 'Python'")
            print("   - 'AWS'")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())