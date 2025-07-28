#!/usr/bin/env python3
"""Standalone script to import test resumes without full app config."""

import json
import os
from datetime import datetime
from uuid import uuid4
import asyncio
import asyncpg
from typing import Optional

# Configuration - Update these values as needed
# Update with your actual database credentials
# Default uses port 5433 as per .env.example
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:your-secure-password@localhost:5433/promtitude")
TEST_USER_EMAIL = "promtitude@gmail.com"
JSON_FILE = "test_resumes_100.json"


async def get_db_connection():
    """Create a database connection."""
    # Parse DATABASE_URL if it starts with postgresql://
    if DATABASE_URL.startswith("postgresql://"):
        # Convert to asyncpg format
        db_url = DATABASE_URL.replace("postgresql://", "postgres://")
    else:
        db_url = DATABASE_URL
    
    try:
        conn = await asyncpg.connect(db_url)
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print(f"   DATABASE_URL: {DATABASE_URL}")
        print("\nPlease set the DATABASE_URL environment variable or update it in this script.")
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


async def import_resumes(conn, user_id: str, json_file: str):
    """Import resumes from JSON file."""
    print(f"\nImporting resumes from {json_file}...")
    
    # Load JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {json_file}")
        print("Please ensure test_resumes_100.json is in the current directory.")
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
            
            # Prepare data
            resume_id = str(uuid4())
            skills_json = json.dumps(resume_data.get('skills', []))
            work_exp_json = json.dumps(resume_data.get('work_experience', []))
            education_json = json.dumps(resume_data.get('education', []))
            
            # Create full text for searching
            full_text = f"{resume_data['first_name']} {resume_data['last_name']} "
            full_text += f"{resume_data.get('current_title', '')} "
            full_text += f"{resume_data.get('summary', '')} "
            full_text += " ".join(resume_data.get('skills', []))
            
            skills_text = " ".join(resume_data.get('skills', []))
            
            # Insert resume
            await conn.execute("""
                INSERT INTO resumes (
                    id, user_id, first_name, last_name, email, phone, location,
                    current_title, summary, years_experience, skills, 
                    work_experience, education, raw_text, full_text, skills_text,
                    status, parse_status, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb, 
                    $12::jsonb, $13::jsonb, $14, $15, $16, $17, $18, $19, $20
                )
            """, 
                resume_id, user_id, resume_data['first_name'], resume_data['last_name'],
                resume_data['email'], resume_data.get('phone'), resume_data.get('location'),
                resume_data.get('current_title'), resume_data.get('summary'),
                resume_data.get('years_experience', 0), skills_json,
                work_exp_json, education_json, json.dumps(resume_data),
                full_text, skills_text, 'active', 'completed',
                datetime.utcnow(), datetime.utcnow()
            )
            
            imported += 1
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ Imported {i + 1} resumes...")
                
        except Exception as e:
            print(f"  ✗ Error importing resume {i + 1}: {e}")
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
    samples = await conn.fetch(
        "SELECT first_name, last_name, current_title FROM resumes WHERE user_id = $1 LIMIT 5",
        user_id
    )
    
    if samples:
        print("\n   Sample resumes:")
        for s in samples:
            print(f"   - {s['first_name']} {s['last_name']} ({s['current_title']})")


async def main():
    """Run the import."""
    print("="*60)
    print("TEST RESUME IMPORT (Standalone)")
    print("="*60)
    
    # Get database connection
    conn = await get_db_connection()
    if not conn:
        return
    
    try:
        # Get or create user
        user_id = await get_or_create_user(conn, TEST_USER_EMAIL)
        if not user_id:
            return
        
        # Import resumes
        await import_resumes(conn, user_id, JSON_FILE)
        
        # Verify
        await verify_import(conn, user_id)
        
        print("\n✅ Import complete! You can now:")
        print("   1. Run vector indexing: python scripts/reindex_all_resumes.py")
        print("   2. Test searches for 'Python', 'AWS', 'William Alves', etc.")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    # Instructions if DATABASE_URL not set
    if not os.getenv("DATABASE_URL"):
        print("⚠️  DATABASE_URL environment variable not set!")
        print("\nPlease set it first:")
        print("  Windows: set DATABASE_URL=postgresql://user:password@localhost/promtitude")
        print("  Linux/Mac: export DATABASE_URL=postgresql://user:password@localhost/promtitude")
        print("\nOr edit the DATABASE_URL variable in this script directly.")
    else:
        asyncio.run(main())