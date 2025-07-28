#!/usr/bin/env python
"""Find William Alves in the database."""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.resume import Resume

async def find_william_alves():
    """Search for William Alves in the database."""
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=== Searching for William Alves ===\n")
        
        # Search for William Alves
        result = await session.execute(
            select(Resume)
            .where(
                and_(
                    Resume.first_name == "William",
                    Resume.last_name == "Alves"
                )
            )
        )
        resumes = result.scalars().all()
        
        if not resumes:
            print("No resume found for William Alves")
            # Let's also check with case-insensitive search
            result = await session.execute(
                select(Resume)
                .where(
                    and_(
                        Resume.first_name.ilike("william"),
                        Resume.last_name.ilike("alves")
                    )
                )
            )
            resumes = result.scalars().all()
            
            if resumes:
                print("Found with case-insensitive search:")
        
        if resumes:
            print(f"Found {len(resumes)} resume(s) for William Alves\n")
            
            for i, resume in enumerate(resumes, 1):
                print(f"Resume #{i}:")
                print(f"  ID: {resume.id}")
                print(f"  Name: {resume.first_name} {resume.last_name}")
                print(f"  Email: {resume.email}")
                print(f"  Phone: {resume.phone}")
                print(f"  Location: {resume.location}")
                print(f"  Current Title: {resume.current_title}")
                print(f"  Years Experience: {resume.years_experience}")
                print(f"  LinkedIn URL: {resume.linkedin_url}")
                print(f"  Status: {resume.status}")
                print(f"  Parse Status: {resume.parse_status}")
                print(f"  Created At: {resume.created_at}")
                print(f"  Updated At: {resume.updated_at}")
                
                print(f"\n  Skills ({len(resume.skills) if resume.skills else 0} total):")
                if resume.skills:
                    for skill in resume.skills:
                        print(f"    - {skill}")
                else:
                    print("    No skills listed")
                
                print(f"\n  Keywords:")
                if resume.keywords:
                    for keyword in resume.keywords:
                        print(f"    - {keyword}")
                else:
                    print("    No keywords listed")
                
                print(f"\n  Summary:")
                if resume.summary:
                    print(f"    {resume.summary}")
                else:
                    print("    No summary")
                
                print("\n" + "="*50 + "\n")
        else:
            print("William Alves not found in the database.")
            
            # Let's check what names we do have
            print("\nChecking for any Alves or William in the database...")
            
            # Search for any Alves
            result = await session.execute(
                select(Resume.first_name, Resume.last_name)
                .where(Resume.last_name == "Alves")
                .limit(5)
            )
            alves_names = result.all()
            
            if alves_names:
                print(f"\nFound {len(alves_names)} people with last name 'Alves':")
                for first_name, last_name in alves_names:
                    print(f"  - {first_name} {last_name}")
            
            # Search for any William
            result = await session.execute(
                select(Resume.first_name, Resume.last_name)
                .where(Resume.first_name == "William")
                .limit(5)
            )
            william_names = result.all()
            
            if william_names:
                print(f"\nFound {len(william_names)} people with first name 'William':")
                for first_name, last_name in william_names:
                    print(f"  - {first_name} {last_name}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(find_william_alves())