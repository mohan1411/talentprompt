#!/usr/bin/env python3
"""Import test resumes from JSON file."""

import asyncio
import json
import sys
import os
from datetime import datetime
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User
from app.models.resume import Resume
from app.services.vector_search import vector_search


async def get_or_create_test_user(db: AsyncSession) -> User:
    """Get or create the test user."""
    email = "promtitude@gmail.com"
    
    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user:
        print(f"✓ Found existing user: {email}")
        return user
    
    # Create user if not exists
    user = User(
        id=uuid4(),
        email=email,
        full_name="Test User",
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow()
    )
    
    db.add(user)
    await db.commit()
    print(f"✓ Created new user: {email}")
    
    return user


async def import_resumes(db: AsyncSession, json_file: str):
    """Import resumes from JSON file."""
    print(f"\nImporting resumes from {json_file}...")
    
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    resumes_data = data.get('resumes', [])
    print(f"Found {len(resumes_data)} resumes to import")
    
    # Get test user
    user = await get_or_create_test_user(db)
    
    # Import resumes
    imported = 0
    skipped = 0
    
    for i, resume_data in enumerate(resumes_data):
        try:
            # Check if resume already exists (by email)
            existing = await db.execute(
                select(Resume).where(
                    Resume.email == resume_data['email'],
                    Resume.user_id == user.id
                )
            )
            if existing.scalar_one_or_none():
                print(f"  - Skipping {resume_data['first_name']} {resume_data['last_name']} (already exists)")
                skipped += 1
                continue
            
            # Create resume
            resume = Resume(
                id=uuid4(),
                user_id=user.id,
                first_name=resume_data['first_name'],
                last_name=resume_data['last_name'],
                email=resume_data['email'],
                phone=resume_data.get('phone'),
                location=resume_data.get('location'),
                current_title=resume_data.get('current_title'),
                summary=resume_data.get('summary'),
                years_experience=resume_data.get('years_experience', 0),
                skills=resume_data.get('skills', []),
                raw_text=json.dumps(resume_data),  # Store full data as raw text
                full_text=f"{resume_data['first_name']} {resume_data['last_name']} "
                         f"{resume_data.get('current_title', '')} "
                         f"{resume_data.get('summary', '')} "
                         f"{' '.join(resume_data.get('skills', []))}",
                skills_text=' '.join(resume_data.get('skills', [])),
                status='active',
                parse_status='completed',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(resume)
            
            # Commit every 10 resumes
            if (i + 1) % 10 == 0:
                await db.commit()
                print(f"  ✓ Imported {i + 1} resumes...")
            
            imported += 1
            
        except Exception as e:
            print(f"  ✗ Error importing resume {i + 1}: {e}")
            continue
    
    # Final commit
    await db.commit()
    
    print(f"\n✅ Import complete!")
    print(f"   - Imported: {imported}")
    print(f"   - Skipped: {skipped}")
    print(f"   - Total in DB for user: {imported + skipped}")
    
    return imported > 0


async def index_resumes_to_vector_db(db: AsyncSession):
    """Index imported resumes to vector database."""
    print("\n" + "="*60)
    print("Indexing resumes to vector database...")
    print("="*60)
    
    # Get test user
    user = await get_or_create_test_user(db)
    
    # Get all resumes for user
    result = await db.execute(
        select(Resume).where(Resume.user_id == user.id)
    )
    resumes = result.scalars().all()
    
    print(f"Found {len(resumes)} resumes to index")
    
    indexed = 0
    errors = 0
    
    for i, resume in enumerate(resumes):
        try:
            # Create searchable text
            searchable_text = f"{resume.first_name} {resume.last_name} "
            if resume.current_title:
                searchable_text += f"{resume.current_title} "
            if resume.summary:
                searchable_text += f"{resume.summary} "
            if resume.skills:
                searchable_text += " ".join(resume.skills)
            
            # Create metadata
            metadata = {
                "user_id": str(resume.user_id),
                "first_name": resume.first_name,
                "last_name": resume.last_name,
                "email": resume.email,
                "current_title": resume.current_title,
                "location": resume.location,
                "years_experience": resume.years_experience,
                "skills": resume.skills or []
            }
            
            # Index in Qdrant
            embedding = await vector_search.index_resume(
                resume_id=str(resume.id),
                text=searchable_text,
                metadata=metadata
            )
            
            if embedding:
                indexed += 1
                if (i + 1) % 10 == 0:
                    print(f"  ✓ Indexed {i + 1} resumes...")
            else:
                errors += 1
                
        except Exception as e:
            errors += 1
            print(f"  ✗ Error indexing resume {resume.id}: {e}")
    
    print(f"\n✅ Vector indexing complete!")
    print(f"   - Indexed: {indexed}")
    print(f"   - Errors: {errors}")


async def main():
    """Run the import process."""
    print("="*60)
    print("TEST RESUME IMPORT TOOL")
    print("="*60)
    
    # Check for JSON file
    json_file = 'test_resumes_100.json'
    if not os.path.exists(json_file):
        print(f"❌ Error: {json_file} not found!")
        print("Please run generate_100_test_resumes.py first.")
        return
    
    # Connect to database
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Import resumes
        success = await import_resumes(db, json_file)
        
        if success:
            # Ask about vector indexing
            response = input("\nDo you want to index these resumes for vector search? (yes/no): ").lower().strip()
            if response == 'yes':
                await index_resumes_to_vector_db(db)
    
    await engine.dispose()
    
    print("\n✅ All done! You can now test searches with these resumes.")
    print("\nTest searches:")
    print('  - "Senior Python developer with AWS"')
    print('  - "William Alves"')
    print('  - "Python"')
    print('  - "AWS"')


if __name__ == "__main__":
    asyncio.run(main())