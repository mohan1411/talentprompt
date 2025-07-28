#!/usr/bin/env python3
"""Debug why William Alves ranks high for Python AWS search."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User
from app.models.resume import Resume
from app.services.search import search_service
from app.services.query_parser import query_parser


async def debug_search():
    """Debug the search results for Python AWS query."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Get mohan.g1411@gmail.com user
            stmt = select(User).where(User.email == "mohan.g1411@gmail.com")
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ User not found!")
                return
                
            print(f"✅ Found user: {user.email}")
            
            # Test query
            query = "Senior Python Developer with AWS"
            print(f"\n🔍 Testing query: '{query}'")
            
            # Parse query
            parsed = query_parser.parse_query(query)
            print(f"\n📝 Parsed query:")
            print(f"  - Required skills: {parsed['skills']}")
            print(f"  - Seniority: {parsed['seniority']}")
            print(f"  - Roles: {parsed['roles']}")
            
            # Perform search
            print("\n🔎 Performing search...")
            results = await search_service.search_resumes(
                db, query, user.id, limit=10
            )
            
            print(f"\n📊 Found {len(results)} results")
            
            # Analyze William Alves specifically
            william_found = False
            
            for i, (resume, score) in enumerate(results, 1):
                if resume['first_name'] == 'William' and resume['last_name'] == 'Alves':
                    william_found = True
                    print(f"\n⚠️  FOUND WILLIAM ALVES at position #{i}")
                    print(f"  Score: {score:.4f}")
                    print(f"  Title: {resume.get('current_title', 'N/A')}")
                    print(f"  Skills: {resume.get('skills', [])}")
                    
                    # Check skill matches
                    resume_skills_lower = [s.lower() for s in resume.get('skills', [])]
                    has_python = any('python' in skill for skill in resume_skills_lower)
                    has_aws = any('aws' in skill for skill in resume_skills_lower)
                    
                    print(f"\n  Skill Analysis:")
                    print(f"    - Has Python: {'✓' if has_python else '✗ MISSING'}")
                    print(f"    - Has AWS: {'✓' if has_aws else '✗'}")
                    print(f"\n  ❌ This candidate should be penalized for missing Python!")
                    
            if not william_found:
                print("\n✅ Good news: William Alves is NOT in the top 10 results!")
            
            # Show top 5 results for comparison
            print("\n" + "="*60)
            print("TOP 5 RESULTS (for comparison):")
            print("="*60)
            
            for i, (resume, score) in enumerate(results[:5], 1):
                print(f"\n{i}. {resume['first_name']} {resume['last_name']} (Score: {score:.4f})")
                print(f"   Title: {resume.get('current_title', 'N/A')}")
                
                # Check skills
                resume_skills_lower = [s.lower() for s in resume.get('skills', [])]
                has_python = any('python' in skill for skill in resume_skills_lower)
                has_aws = any('aws' in skill for skill in resume_skills_lower)
                
                print(f"   Python: {'✓' if has_python else '✗'} | AWS: {'✓' if has_aws else '✗'}")
                print(f"   All skills: {', '.join(resume.get('skills', [])[:6])}...")
                
        finally:
            await engine.dispose()


async def main():
    """Main function."""
    print("="*70)
    print("DEBUG: Why is William Alves ranking high?")
    print("="*70)
    
    await debug_search()


if __name__ == "__main__":
    asyncio.run(main())