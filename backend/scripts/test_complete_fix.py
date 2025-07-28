#!/usr/bin/env python3
"""Test the complete search fix."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.user import User
from app.services.query_parser import query_parser
from app.services.search import search_service


async def test_complete_fix():
    """Test the complete search fix with real data."""
    print("Testing Complete Search Fix")
    print("=" * 70)
    
    # Test 1: Query Parser
    print("\n1. Testing Query Parser:")
    query = "Senior Python Developer with AWS"
    parsed = query_parser.parse_query(query)
    print(f"   Query: '{query}'")
    print(f"   Extracted skills: {parsed['skills']}")
    
    if 'r' in parsed['skills']:
        print("   ❌ FAIL: Parser still extracting 'r' from 'Developer'")
        return False
    else:
        print("   ✅ PASS: Parser correctly extracts only ['python', 'aws']")
    
    # Test 2: Find a user with resumes
    print("\n2. Finding user with resumes:")
    async with async_session_maker() as db:
        # Try different users
        test_users = ["mohan.g1411@gmail.com", "promtitude@gmail.com", "admin@promtitude.com"]
        user_with_resumes = None
        
        for email in test_users:
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            if user:
                # Count resumes
                from app.models.resume import Resume
                count_result = await db.execute(
                    select(Resume).where(Resume.user_id == user.id)
                )
                resumes = count_result.scalars().all()
                print(f"   {email}: {len(resumes)} resumes")
                if len(resumes) > 0 and not user_with_resumes:
                    user_with_resumes = user
        
        if not user_with_resumes:
            print("   ❌ No users with resumes found")
            return False
        
        print(f"   ✅ Using {user_with_resumes.email} for testing")
        
        # Test 3: Perform search
        print(f"\n3. Testing search for '{query}':")
        results = await search_service.search_resumes(
            db,
            query=query,
            user_id=user_with_resumes.id,
            limit=10
        )
        
        print(f"   Found {len(results)} results")
        
        if results:
            print("\n   Top 5 results:")
            for i, (resume, score) in enumerate(results[:5], 1):
                skills = resume.get('skills', [])
                skills_lower = [s.lower() for s in skills if s]
                
                has_python = any('python' in s for s in skills_lower)
                has_aws = any('aws' in s for s in skills_lower)
                
                skill_status = []
                if has_python:
                    skill_status.append("✓ Python")
                else:
                    skill_status.append("✗ Python")
                    
                if has_aws:
                    skill_status.append("✓ AWS")
                else:
                    skill_status.append("✗ AWS")
                
                print(f"   {i}. {resume['first_name']} {resume['last_name']} - Score: {score:.3f}")
                print(f"      Skills: {', '.join(skills[:5])}...")
                print(f"      Match: {' | '.join(skill_status)}")
                
                # Check if William Alves is still ranking high
                if resume['first_name'] == 'William' and resume['last_name'] == 'Alves':
                    if not has_python and score > 0.5:
                        print(f"      ❌ William Alves still ranking too high without Python!")
        
        print("\n" + "=" * 70)
        print("Test completed!")
        return True


if __name__ == "__main__":
    success = asyncio.run(test_complete_fix())
    sys.exit(0 if success else 1)