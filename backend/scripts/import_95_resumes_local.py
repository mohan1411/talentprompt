#!/usr/bin/env python3
"""
Import the 95 resumes from local machine using public database URL.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from uuid import UUID, uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# IMPORTANT: Replace with your actual public Railway database URL
PUBLIC_DATABASE_URL = input("Paste your PUBLIC Railway database URL (from Railway dashboard): ").strip()

if not PUBLIC_DATABASE_URL or "railway.internal" in PUBLIC_DATABASE_URL:
    print("❌ Please provide the PUBLIC database URL, not the internal one!")
    print("   Get it from your Railway dashboard → Database → Connect → Public URL")
    sys.exit(1)

# Override the settings
os.environ['DATABASE_URL'] = PUBLIC_DATABASE_URL

from app.db.session import async_session_maker as async_session
from app.models.user import User
from app.models.resume import Resume
from app.services.resume_processor import resume_processor
from app.core.config import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def import_resumes():
    print("="*60)
    print("IMPORTING 95 RESUMES (LOCAL → PRODUCTION)")
    print("="*60)
    
    # Check for import file
    import_file = Path("backend/scripts/promtitude_95_resumes_export.json")
    if not import_file.exists():
        import_file = Path("scripts/promtitude_95_resumes_export.json")
    
    if not import_file.exists():
        print(f"❌ Import file not found!")
        return
    
    # Load the data
    print(f"\n1. Loading {import_file}...")
    with open(import_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"   Export date: {data['export_date']}")
    print(f"   User email: {data['user_email']}")
    print(f"   Resume count: {data['resume_count']}")
    
    async with async_session() as db:
        # Get or create user
        print("\n2. Checking user...")
        result = await db.execute(
            select(User).where(User.email == "promtitude@gmail.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("   User not found. Creating promtitude@gmail.com...")
            user = User(
                id=uuid4(),
                email="promtitude@gmail.com",
                full_name="Promtitude Test User",
                is_active=True,
                is_verified=True,
                oauth_provider="google"
            )
            db.add(user)
            await db.commit()
            print(f"   ✅ Created user with ID: {user.id}")
        else:
            print(f"   ✅ Found existing user with ID: {user.id}")
        
        # Check existing resumes
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user.id)
            .where(Resume.status != 'deleted')
        )
        existing_resumes = result.scalars().all()
        
        if existing_resumes:
            print(f"\n⚠️  User already has {len(existing_resumes)} active resumes")
            choice = input("Delete existing and import new? (yes/no): ").lower().strip()
            
            if choice == "yes":
                print("\n   Deleting existing resumes...")
                for resume in existing_resumes:
                    resume.status = 'deleted'
                    resume.updated_at = datetime.utcnow()
                await db.commit()
                print(f"   ✅ Soft-deleted {len(existing_resumes)} existing resumes")
            else:
                print("Import cancelled.")
                return
        
        # Import resumes
        print(f"\n3. Importing {len(data['resumes'])} resumes...")
        
        success_count = 0
        error_count = 0
        
        for i, resume_data in enumerate(data['resumes']):
            try:
                resume = Resume(
                    id=uuid4(),
                    user_id=user.id,
                    first_name=resume_data['first_name'],
                    last_name=resume_data['last_name'],
                    email=resume_data.get('email'),
                    phone=resume_data.get('phone'),
                    location=resume_data.get('location'),
                    summary=resume_data.get('summary'),
                    skills=resume_data.get('skills', []),
                    keywords=resume_data.get('keywords', []),
                    current_title=resume_data.get('current_title'),
                    years_experience=resume_data.get('years_experience'),
                    job_position=resume_data.get('job_position'),
                    raw_text=resume_data['raw_text'],
                    original_filename=resume_data['original_filename'],
                    file_size=resume_data['file_size'],
                    file_type=resume_data['file_type'],
                    linkedin_url=resume_data.get('linkedin_url'),
                    parsed_data=resume_data.get('parsed_data'),
                    status='active',
                    parse_status='completed',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    parsed_at=datetime.utcnow(),
                    view_count=resume_data.get('view_count', 0),
                    search_appearance_count=resume_data.get('search_appearance_count', 0)
                )
                
                db.add(resume)
                
                if (i + 1) % 10 == 0:
                    await db.commit()
                    print(f"   Progress: {i + 1}/{len(data['resumes'])} imported...")
                
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ Error importing resume {i + 1}: {str(e)}")
                error_count += 1
        
        await db.commit()
        
        print(f"\n✅ Import complete!")
        print(f"   Successfully imported: {success_count}")
        print(f"   Errors: {error_count}")
        
        print("\n4. Note: Vector indexing will happen when resumes are accessed")
        print("   The first search may be slower as embeddings are generated")

if __name__ == "__main__":
    print("This script imports resumes from your LOCAL machine to Railway PRODUCTION")
    print("Make sure you have the PUBLIC database URL from Railway dashboard")
    print("")
    
    try:
        asyncio.run(import_resumes())
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()