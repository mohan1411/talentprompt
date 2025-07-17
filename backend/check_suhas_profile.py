#!/usr/bin/env python3
"""Check Suhas's profile in the database."""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app.models.resume import Resume
from app.core.config import settings

async def check_suhas_profile():
    """Check if Suhas's profile exists and what skills are stored."""
    
    # Create engine and session
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Search for Suhas's profile
        result = await session.execute(
            select(Resume).where(Resume.linkedin_url.like('%shudgur%'))
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            print("❌ Suhas's profile NOT FOUND in database")
            print(f"   LinkedIn URL searched: %shudgur%")
            
            # Check all LinkedIn profiles
            all_profiles = await session.execute(
                select(Resume.first_name, Resume.last_name, Resume.linkedin_url)
                .where(Resume.linkedin_url.isnot(None))
                .limit(10)
            )
            print("\n📋 Sample LinkedIn profiles in database:")
            for p in all_profiles:
                print(f"   - {p.first_name} {p.last_name}: {p.linkedin_url}")
        else:
            print(f"✅ Found profile: {profile.first_name} {profile.last_name}")
            print(f"   LinkedIn URL: {profile.linkedin_url}")
            print(f"   Current Title: {profile.current_title}")
            print(f"   Years Experience: {profile.years_experience}")
            print(f"   Created: {profile.created_at}")
            print(f"   Last LinkedIn Sync: {profile.last_linkedin_sync}")
            
            # Check skills
            print(f"\n🎯 Skills stored in database:")
            if profile.skills:
                if isinstance(profile.skills, list):
                    print(f"   Skills count: {len(profile.skills)}")
                    for skill in profile.skills:
                        print(f"   - {skill}")
                else:
                    print(f"   Skills type: {type(profile.skills)}")
                    print(f"   Skills raw: {profile.skills}")
            else:
                print("   ❌ No skills stored")
            
            # Check expected skills
            expected_skills = ["Kaizen", "Strategy", "Employee Training", "Project Management"]
            print(f"\n🔍 Checking for expected skills:")
            
            found_skills = []
            missing_skills = []
            
            if profile.skills and isinstance(profile.skills, list):
                for expected in expected_skills:
                    found = False
                    for skill in profile.skills:
                        if expected.lower() in skill.lower():
                            found = True
                            found_skills.append(f"{expected} (found as: {skill})")
                            break
                    if not found:
                        missing_skills.append(expected)
            else:
                missing_skills = expected_skills
            
            print(f"   ✅ Found: {found_skills}")
            print(f"   ❌ Missing: {missing_skills}")
            
            # Check raw_text for skills
            print(f"\n📄 Checking raw_text for skills:")
            if profile.raw_text:
                for skill in expected_skills:
                    if skill.lower() in profile.raw_text.lower():
                        print(f"   ✅ '{skill}' found in raw_text")
                    else:
                        print(f"   ❌ '{skill}' NOT found in raw_text")
            else:
                print("   ❌ No raw_text stored")
            
            # Check LinkedIn data
            print(f"\n📊 LinkedIn data stored:")
            if profile.linkedin_data:
                if 'skills' in profile.linkedin_data:
                    linkedin_skills = profile.linkedin_data.get('skills', [])
                    print(f"   Skills in linkedin_data: {len(linkedin_skills)}")
                    for skill in linkedin_skills[:10]:  # Show first 10
                        print(f"   - {skill}")
                else:
                    print("   ❌ No skills in linkedin_data")
            else:
                print("   ❌ No linkedin_data stored")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_suhas_profile())