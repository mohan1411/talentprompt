#!/usr/bin/env python3
"""
Import the 95 resumes to production - Railway version.
This version is designed to work in Railway's environment.
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

from app.db.session import async_session_maker as async_session
from app.models.user import User
from app.models.resume import Resume
from app.services.resume_processor import resume_processor
from app.core.config import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

async def import_resumes_to_prod():
    print("="*60, flush=True)
    print("IMPORTING 95 RESUMES TO PRODUCTION (RAILWAY)", flush=True)
    print("="*60, flush=True)
    
    # Check for import file
    import_file = "promtitude_95_resumes_export.json"
    if not Path(import_file).exists():
        # Try in scripts directory
        script_dir = Path(__file__).parent
        import_file = script_dir / "promtitude_95_resumes_export.json"
        
        if not import_file.exists():
            print(f"❌ Import file not found!", flush=True)
            print(f"   Looked in: {os.getcwd()}", flush=True)
            print(f"   Also tried: {import_file}", flush=True)
            return
    
    # Load the data
    print(f"\n1. Loading {import_file}...", flush=True)
    with open(import_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"   Export date: {data['export_date']}", flush=True)
    print(f"   User email: {data['user_email']}", flush=True)
    print(f"   Resume count: {data['resume_count']}", flush=True)
    
    # In Railway, auto-confirm
    print("\n🚀 Running in Railway environment - auto-confirming actions", flush=True)
    
    async with async_session() as db:
        # Get or create user
        print("\n2. Checking user...", flush=True)
        result = await db.execute(
            select(User).where(User.email == "promtitude@gmail.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("   User not found. Creating promtitude@gmail.com...", flush=True)
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
            print(f"   ✅ Created user with ID: {user.id}", flush=True)
        else:
            print(f"   ✅ Found existing user with ID: {user.id}", flush=True)
        
        # Check existing resumes
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user.id)
            .where(Resume.status != 'deleted')
        )
        existing_resumes = result.scalars().all()
        
        if existing_resumes:
            print(f"\n⚠️  User already has {len(existing_resumes)} active resumes", flush=True)
            print("   Auto-selecting: Delete existing and import new", flush=True)
            
            # Delete existing
            print("\n   Deleting existing resumes...", flush=True)
            for resume in existing_resumes:
                resume.status = 'deleted'
                resume.updated_at = datetime.utcnow()
            await db.commit()
            print(f"   ✅ Soft-deleted {len(existing_resumes)} existing resumes", flush=True)
        
        # Import resumes
        print(f"\n3. Importing {len(data['resumes'])} resumes...", flush=True)
        
        success_count = 0
        error_count = 0
        
        for i, resume_data in enumerate(data['resumes']):
            try:
                # Create new resume with new ID (don't reuse old IDs)
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
                    parse_status='completed',  # Already parsed
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    parsed_at=datetime.utcnow(),
                    view_count=resume_data.get('view_count', 0),
                    search_appearance_count=resume_data.get('search_appearance_count', 0)
                )
                
                db.add(resume)
                
                # Commit every 10 resumes
                if (i + 1) % 10 == 0:
                    await db.commit()
                    print(f"   Progress: {i + 1}/{len(data['resumes'])} imported...", flush=True)
                
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ Error importing resume {i + 1}: {str(e)}", flush=True)
                error_count += 1
        
        # Final commit
        await db.commit()
        
        print(f"\n✅ Import complete!", flush=True)
        print(f"   Successfully imported: {success_count}", flush=True)
        print(f"   Errors: {error_count}", flush=True)
        
        # Trigger vector indexing
        if settings.OPENAI_API_KEY and settings.QDRANT_URL:
            print("\n4. Indexing resumes for vector search...", flush=True)
            print(f"   OpenAI API Key: {'Set' if settings.OPENAI_API_KEY else 'Not set'}", flush=True)
            print(f"   Qdrant URL: {settings.QDRANT_URL if settings.QDRANT_URL else 'Not set'}", flush=True)
            
            # Get all imported resumes
            result = await db.execute(
                select(Resume)
                .where(Resume.user_id == user.id)
                .where(Resume.status != 'deleted')
                .order_by(Resume.created_at.desc())
                .limit(success_count)
            )
            imported_resumes = result.scalars().all()
            
            # Queue for processing
            indexed_count = 0
            for resume in imported_resumes:
                try:
                    # Process synchronously for better error handling in Railway
                    await resume_processor.process_resume(str(resume.id))
                    indexed_count += 1
                    if indexed_count % 10 == 0:
                        print(f"   Indexed {indexed_count}/{len(imported_resumes)} resumes...", flush=True)
                except Exception as e:
                    print(f"   ⚠️  Failed to index {resume.first_name} {resume.last_name}: {str(e)}", flush=True)
            
            print(f"   ✅ Indexed {indexed_count} resumes", flush=True)
        else:
            print("\n⚠️  Vector search not configured - skipping indexing", flush=True)
            print("   Set OPENAI_API_KEY and QDRANT_URL to enable vector search", flush=True)
        
        print("\n" + "="*60, flush=True)
        print("IMPORT SUMMARY", flush=True)
        print("="*60, flush=True)
        print(f"\n✅ Successfully imported {success_count} resumes for promtitude@gmail.com", flush=True)
        print("\nNext steps:", flush=True)
        print("1. Log in as promtitude@gmail.com on production", flush=True)
        print("2. Verify you see 95 resumes", flush=True)
        print("3. Test search functionality", flush=True)

if __name__ == "__main__":
    print("Starting import process...", flush=True)
    try:
        asyncio.run(import_resumes_to_prod())
    except Exception as e:
        print(f"❌ Import failed with error: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()