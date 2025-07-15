#!/usr/bin/env python3
"""Test script to verify JSON column queries work correctly."""

import asyncio
import sys
from sqlalchemy import select, func, String, or_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.insert(0, '/mnt/d/Projects/AI/BusinessIdeas/SmallBusiness/TalentPrompt/backend')

from app.models.resume import Resume
from app.core.config import settings

async def test_json_queries():
    """Test different JSON query patterns."""
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("\n1. Testing skills JSON query with cast to string:")
        try:
            # Test the fixed query pattern
            skill_to_find = "Python"
            stmt = select(Resume).where(
                func.cast(Resume.skills, String).ilike(f'%"{skill_to_find}"%')
            ).limit(5)
            
            result = await session.execute(stmt)
            resumes = result.scalars().all()
            print(f"Found {len(resumes)} resumes with skill '{skill_to_find}'")
            
            for resume in resumes:
                print(f"- {resume.first_name} {resume.last_name}: {resume.skills}")
        
        except Exception as e:
            print(f"Error in skills query: {e}")
        
        print("\n2. Testing count query with JSON cast:")
        try:
            # Test the count query pattern
            keyword = "python"
            count_stmt = select(func.count(Resume.id)).where(
                Resume.status == 'active',
                or_(
                    Resume.summary.ilike(f"%{keyword}%"),
                    Resume.current_title.ilike(f"%{keyword}%"),
                    func.cast(Resume.skills, String).ilike(f'%"{keyword}"%')
                )
            )
            
            count_result = await session.execute(count_stmt)
            count = count_result.scalar() or 0
            print(f"Found {count} resumes matching '{keyword}'")
            
        except Exception as e:
            print(f"Error in count query: {e}")
        
        print("\n3. Testing multiple skills filter:")
        try:
            # Test filtering by multiple skills
            skills_to_find = ["Python", "Django", "AWS"]
            stmt = select(Resume).where(Resume.status == 'active')
            
            for skill in skills_to_find:
                stmt = stmt.where(
                    func.cast(Resume.skills, String).ilike(f'%"{skill}"%')
                )
            
            stmt = stmt.limit(5)
            
            result = await session.execute(stmt)
            resumes = result.scalars().all()
            print(f"Found {len(resumes)} resumes with all skills: {skills_to_find}")
            
            for resume in resumes:
                print(f"- {resume.first_name} {resume.last_name}: {resume.skills}")
                
        except Exception as e:
            print(f"Error in multiple skills query: {e}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_json_queries())