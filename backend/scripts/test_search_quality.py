#!/usr/bin/env python3
"""Test the enhanced search quality with skill matching."""

import asyncio
import sys
from pathlib import Path
from typing import List, Tuple
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func

from app.core.config import settings
from app.models.user import User
from app.models.resume import Resume
from app.services.search import search_service
from app.services.search_metrics import search_metrics
from app.services.query_parser import query_parser


async def test_search_quality(user_email: str = "promtitude@gmail.com"):
    """Test search quality with various queries."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Get user
            stmt = select(User).where(User.email == user_email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User {user_email} not found!")
                return
            
            print(f"✅ Found user: {user.email}")
            
            # Count resumes with specific skills
            await analyze_skill_distribution(db, user.id)
            
            # Test queries
            test_queries = [
                "Senior Python Developer with AWS",
                "Python AWS Docker",
                "JavaScript React Node.js",
                "Java Spring Boot AWS",
                "Machine Learning Engineer with TensorFlow",
                "DevOps Engineer Kubernetes Docker",
                "Full Stack Developer Python React",
                "Data Scientist Python R",
                "Mobile Developer React Native",
                "Cloud Architect AWS Azure"
            ]
            
            print("\n" + "="*70)
            print("TESTING ENHANCED SEARCH QUALITY")
            print("="*70)
            
            for query in test_queries:
                print(f"\n{'='*60}")
                print(f"Query: '{query}'")
                print("="*60)
                
                # Parse query to show what we're looking for
                parsed = query_parser.parse_query(query)
                print(f"Required skills: {', '.join(parsed['skills'])}")
                
                # Perform search
                results = await search_service.search_resumes(
                    db, query, user.id, limit=10
                )
                
                print(f"\nFound {len(results)} results")
                
                # Show top 5 results with skill analysis
                if results:
                    print("\nTop 5 Results:")
                    for i, (resume, score) in enumerate(results[:5], 1):
                        print(f"\n{i}. {resume['first_name']} {resume['last_name']}")
                        print(f"   Title: {resume.get('current_title', 'N/A')}")
                        print(f"   Score: {score:.3f}")
                        
                        # Check skill matches
                        if parsed['skills'] and resume.get('skills'):
                            resume_skills_lower = [s.lower() for s in resume['skills']]
                            matched = []
                            missing = []
                            
                            for skill in parsed['skills']:
                                if any(skill in rs for rs in resume_skills_lower):
                                    matched.append(f"✓ {skill}")
                                else:
                                    missing.append(f"✗ {skill}")
                            
                            print(f"   Skill matches: {', '.join(matched)}")
                            if missing:
                                print(f"   Missing: {', '.join(missing)}")
                        
                        print(f"   All skills: {', '.join(resume.get('skills', [])[:8])}...")
            
            # Display metrics summary
            print("\n" + "="*70)
            print("SEARCH QUALITY METRICS SUMMARY")
            print("="*70)
            
            summary = search_metrics.get_summary_stats()
            for key, value in summary.items():
                print(f"{key}: {value}")
            
            # Show queries with issues
            recent = search_metrics.get_recent_searches()
            queries_with_issues = [s for s in recent if s['issues']]
            
            if queries_with_issues:
                print(f"\n⚠️  Queries with quality issues ({len(queries_with_issues)}):")
                for search in queries_with_issues:
                    print(f"\n  Query: '{search['query']}'")
                    for issue in search['issues']:
                        print(f"    - {issue}")
            
        finally:
            await engine.dispose()


async def analyze_skill_distribution(db: AsyncSession, user_id):
    """Analyze skill distribution in the database."""
    print("\n📊 SKILL DISTRIBUTION ANALYSIS")
    print("-"*50)
    
    # Count resumes with specific skill combinations
    skill_combos = [
        ["python", "aws"],
        ["javascript", "react"],
        ["java", "spring boot"],
        ["python", "django"],
        ["node.js", "mongodb"],
        ["docker", "kubernetes"]
    ]
    
    for combo in skill_combos:
        count = 0
        stmt = select(Resume).where(
            Resume.user_id == user_id,
            Resume.status == 'active'
        )
        result = await db.execute(stmt)
        
        for resume in result.scalars():
            if resume.skills:
                skills_lower = [s.lower() for s in resume.skills]
                if all(any(skill in s for s in skills_lower) for skill in combo):
                    count += 1
        
        print(f"  {' + '.join(combo)}: {count} resumes")


async def main():
    """Main function."""
    print("🔍 ENHANCED SEARCH QUALITY TESTER")
    print("="*70)
    print("\nThis script tests the enhanced skill matching algorithm")
    print("It will show how well the search prioritizes candidates with required skills")
    
    # Clear previous metrics
    search_metrics.clear_history()
    
    await test_search_quality()
    
    print("\n✅ Search quality testing complete!")
    print("\nKey improvements implemented:")
    print("  1. Query parser extracts individual skills")
    print("  2. Hybrid scoring combines vector similarity with skill matches")
    print("  3. Candidates with all required skills rank higher")
    print("  4. Search metrics track quality and identify issues")


if __name__ == "__main__":
    asyncio.run(main())