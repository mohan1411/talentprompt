#!/usr/bin/env python
"""Check skills data in the database and test search functionality."""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, select, func, String, cast, or_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.resume import Resume
from app.services.search_skill_fix import create_skill_search_conditions

async def check_skills_data():
    """Check what skills are actually stored in the database."""
    
    # Create async engine
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=== Checking Skills Data in Database ===\n")
        
        # 1. Check if we have any resumes with skills
        result = await session.execute(
            select(func.count(Resume.id)).where(
                Resume.skills.isnot(None),
                func.jsonb_array_length(Resume.skills.cast(text("jsonb"))) > 0
            )
        )
        resumes_with_skills = result.scalar()
        print(f"Resumes with skills: {resumes_with_skills}")
        
        # 2. Get all unique skills
        result = await session.execute(
            select(Resume.id, Resume.first_name, Resume.last_name, Resume.skills, Resume.linkedin_url)
            .where(Resume.skills.isnot(None))
            .limit(10)
        )
        resumes = result.all()
        
        print("\n=== Sample Resumes with Skills ===")
        all_skills = set()
        for resume in resumes:
            if resume.skills:
                print(f"\n{resume.first_name} {resume.last_name} (ID: {resume.id})")
                if resume.linkedin_url:
                    print(f"LinkedIn: {resume.linkedin_url}")
                print(f"Skills: {resume.skills}")
                for skill in resume.skills:
                    all_skills.add(skill)
        
        # 3. Check for WebSphere specifically
        print("\n\n=== Checking for WebSphere Skills ===")
        websphere_variations = ['WebSphere', 'websphere', 'web sphere', 'Websphere', 'WEBSPHERE']
        
        for variation in websphere_variations:
            # Check using ILIKE on cast
            result = await session.execute(
                select(func.count(Resume.id)).where(
                    cast(Resume.skills, String).ilike(f'%{variation}%')
                )
            )
            count = result.scalar()
            print(f"'{variation}' (ILIKE on cast): {count} resumes")
            
            # Check using JSON containment
            result = await session.execute(
                select(func.count(Resume.id)).where(
                    cast(Resume.skills, String).ilike(f'%"{variation}"%')
                )
            )
            count = result.scalar()
            print(f"'{variation}' (with quotes): {count} resumes")
        
        # 4. Test the actual search conditions
        print("\n\n=== Testing Search Conditions ===")
        conditions = create_skill_search_conditions("WebSphere", Resume)
        print(f"Number of search conditions created: {len(conditions)}")
        
        # Test combined conditions
        result = await session.execute(
            select(Resume.id, Resume.first_name, Resume.last_name, Resume.skills)
            .where(or_(*conditions))
            .limit(5)
        )
        search_results = result.all()
        
        print(f"\nSearch results for 'WebSphere': {len(search_results)} found")
        for res in search_results:
            print(f"- {res.first_name} {res.last_name}: {res.skills}")
        
        # 5. Check Anil's profile specifically
        print("\n\n=== Checking Anil's Profile ===")
        result = await session.execute(
            select(Resume)
            .where(Resume.linkedin_url.like('%anil-narasimhappa%'))
            .limit(1)
        )
        anil = result.scalar_one_or_none()
        
        if anil:
            print(f"Found Anil's profile (ID: {anil.id})")
            print(f"Skills: {anil.skills}")
            print(f"Skills data type: {type(anil.skills)}")
            if anil.skills:
                print(f"Number of skills: {len(anil.skills)}")
                print("WebSphere in skills?", any('websphere' in s.lower() for s in anil.skills if s))
        else:
            print("Anil's profile not found!")
        
        # 5b. Check Suhas's profile specifically
        print("\n\n=== Checking Suhas's Profile ===")
        result = await session.execute(
            select(Resume)
            .where(Resume.linkedin_url.like('%shudgur%'))
            .limit(1)
        )
        suhas = result.scalar_one_or_none()
        
        if suhas:
            print(f"Found Suhas's profile (ID: {suhas.id})")
            print(f"Name: {suhas.first_name} {suhas.last_name}")
            print(f"LinkedIn URL: {suhas.linkedin_url}")
            print(f"Skills: {suhas.skills}")
            print(f"Skills data type: {type(suhas.skills)}")
            if suhas.skills:
                print(f"Number of skills: {len(suhas.skills)}")
                # Check for expected skills
                expected_skills = ["Kaizen", "Strategy", "Employee Training", "Project Management"]
                for expected in expected_skills:
                    found = any(expected.lower() in s.lower() for s in suhas.skills if s)
                    print(f"  {expected}: {'✓' if found else '✗'}")
            else:
                print("  No skills stored!")
            
            # Check raw_text
            if suhas.raw_text:
                print(f"\nChecking raw_text for skills:")
                expected_skills = ["Kaizen", "Strategy", "Employee Training", "Project Management"]
                for skill in expected_skills:
                    if skill.lower() in suhas.raw_text.lower():
                        print(f"  {skill}: ✓ (found in raw_text)")
                    else:
                        print(f"  {skill}: ✗ (NOT in raw_text)")
        else:
            print("Suhas's profile not found!")
        
        # 6. Raw SQL query to check JSON data
        print("\n\n=== Raw SQL Query Test ===")
        raw_query = text("""
            SELECT id, first_name, last_name, skills::text 
            FROM resumes 
            WHERE skills::text ILIKE '%websphere%' 
            OR skills::text ILIKE '%WebSphere%'
            LIMIT 5
        """)
        result = await session.execute(raw_query)
        raw_results = result.all()
        
        print(f"Raw SQL results: {len(raw_results)} found")
        for r in raw_results:
            print(f"- {r.first_name} {r.last_name}: {r.skills}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_skills_data())