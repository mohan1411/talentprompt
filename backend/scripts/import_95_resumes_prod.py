#!/usr/bin/env python3
"""
Import the 95 resumes to production for promtitude@gmail.com.
Run this on your production environment.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from uuid import UUID, uuid4

sys.path.append('..')

from app.db.session import async_session_maker as async_session
from app.models.user import User
from app.models.resume import Resume
from app.services.resume_processor import resume_processor
from app.core.config import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def import_resumes_to_prod():
    print("="*60)
    print("IMPORTING 95 RESUMES TO PRODUCTION")
    print("="*60)
    
    # Check for import file
    import_file = "promtitude_95_resumes_export.json"
    if not Path(import_file).exists():
        print(f"❌ Import file '{import_file}' not found!")
        print("   Please upload the export file from your local environment.")
        return
    
    # Load the data
    print(f"\n1. Loading {import_file}...")
    with open(import_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"   Export date: {data['export_date']}")
    print(f"   User email: {data['user_email']}")
    print(f"   Resume count: {data['resume_count']}")
    
    if data['resume_count'] != 95:
        print(f"\n⚠️  WARNING: Expected 95 resumes but file contains {data['resume_count']}")
        confirm = input("Continue anyway? (yes/no): ").lower().strip()
        if confirm != "yes":
            print("Import cancelled.")
            return
    
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
            print("   Options:")
            print("   1. Delete existing and import new (RECOMMENDED)")
            print("   2. Add to existing resumes")
            print("   3. Cancel")
            
            choice = input("\nChoose option (1/2/3): ").strip()
            
            if choice == "1":
                print("\n   Deleting existing resumes...")
                for resume in existing_resumes:
                    resume.status = 'deleted'
                    resume.updated_at = datetime.utcnow()
                await db.commit()
                print(f"   ✅ Soft-deleted {len(existing_resumes)} existing resumes")
            elif choice == "3":
                print("Import cancelled.")
                return
        
        # Import resumes
        print(f"\n3. Importing {len(data['resumes'])} resumes...")
        
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
                    print(f"   Progress: {i + 1}/{len(data['resumes'])} imported...")
                
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ Error importing resume {i + 1}: {str(e)}")
                error_count += 1
        
        # Final commit
        await db.commit()
        
        print(f"\n✅ Import complete!")
        print(f"   Successfully imported: {success_count}")
        print(f"   Errors: {error_count}")
        
        # Trigger vector indexing
        if settings.OPENAI_API_KEY and settings.QDRANT_URL:
            print("\n4. Indexing resumes for vector search...")
            print("   This will run in the background...")
            
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
                    # Process in background
                    asyncio.create_task(
                        resume_processor.process_resume_background(str(resume.id))
                    )
                    indexed_count += 1
                except Exception as e:
                    print(f"   ⚠️  Failed to queue {resume.first_name} {resume.last_name}: {str(e)}")
            
            print(f"   ✅ Queued {indexed_count} resumes for vector indexing")
            print("   Note: Indexing will complete in the background (may take a few minutes)")
        else:
            print("\n⚠️  Vector search not configured - skipping indexing")
            print("   Set OPENAI_API_KEY and QDRANT_URL to enable vector search")
        
        print("\n" + "="*60)
        print("VERIFICATION STEPS")
        print("="*60)
        print("\n1. Log in as promtitude@gmail.com")
        print("2. Check the resumes page - should show 95 resumes")
        print("3. Test Mind Reader Search with queries like:")
        print("   - 'Python developer'")
        print("   - 'Senior engineer with AWS'")
        print("   - 'React TypeScript'")
        print("4. Compare results with your local environment")

if __name__ == "__main__":
    print("\n⚠️  This script will import 95 resumes to PRODUCTION")
    print("   Make sure you're running this on your production server!")
    
    confirm = input("\nAre you on PRODUCTION? (yes/no): ").lower().strip()
    if confirm == "yes":
        asyncio.run(import_resumes_to_prod())
    else:
        print("Import cancelled. Run this script on your production server.")