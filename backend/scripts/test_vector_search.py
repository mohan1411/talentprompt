#!/usr/bin/env python3
"""Comprehensive vector search testing for promtitude@gmail.com."""

import asyncio
import time
import sys
from pathlib import Path
from typing import List, Dict, Any
from statistics import mean, median

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func

from app.core.config import settings
from app.models.user import User
from app.models.resume import Resume
from app.services.search import search_service
from app.services.vector_search import vector_search


class VectorSearchTester:
    """Test vector search functionality comprehensively."""
    
    def __init__(self, user_email: str = "promtitude@gmail.com"):
        self.user_email = user_email
        self.results = {
            "skill_searches": [],
            "role_searches": [],
            "location_searches": [],
            "complex_searches": [],
            "performance": [],
            "relevance_scores": []
        }
    
    async def run_all_tests(self):
        """Run all vector search tests."""
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            # Get user
            stmt = select(User).where(User.email == self.user_email)
            result = await db.execute(stmt)
            self.user = result.scalar_one()
            
            print(f"\n{'='*70}")
            print(f"VECTOR SEARCH TEST SUITE FOR {self.user_email}")
            print(f"{'='*70}\n")
            
            # Run test categories
            await self._test_basic_info(db)
            await self._test_skill_searches(db)
            await self._test_role_searches(db)
            await self._test_location_searches(db)
            await self._test_complex_searches(db)
            await self._test_performance(db)
            await self._analyze_results()
            
        await engine.dispose()
    
    async def _test_basic_info(self, db: AsyncSession):
        """Display basic information."""
        # Count resumes
        count_stmt = select(func.count(Resume.id)).where(
            Resume.user_id == self.user.id,
            Resume.status == 'active'
        )
        count_result = await db.execute(count_stmt)
        resume_count = count_result.scalar()
        
        # Get Qdrant info
        qdrant_info = await vector_search.get_collection_info()
        
        print("📊 BASIC INFORMATION")
        print(f"  User ID: {self.user.id}")
        print(f"  PostgreSQL resumes: {resume_count}")
        print(f"  Qdrant total points: {qdrant_info.get('points_count', 0)}")
        print()
    
    async def _test_skill_searches(self, db: AsyncSession):
        """Test skill-based searches."""
        print("🔧 SKILL-BASED SEARCHES")
        print("-" * 50)
        
        skill_queries = [
            "python",
            "javascript",
            "react",
            "aws",
            "docker",
            "machine learning",
            "tensorflow",
            "kubernetes",
            "graphql",
            "mongodb"
        ]
        
        for query in skill_queries:
            start_time = time.time()
            results = await search_service.search_resumes(db, query, self.user.id, limit=10)
            elapsed = time.time() - start_time
            
            self.results["skill_searches"].append({
                "query": query,
                "count": len(results),
                "time": elapsed,
                "top_scores": [score for _, score in results[:3]]
            })
            
            print(f"\n  Query: '{query}'")
            print(f"  Found: {len(results)} results in {elapsed:.3f}s")
            
            if results:
                print("  Top 3 matches:")
                for i, (resume, score) in enumerate(results[:3], 1):
                    skills_match = query.lower() in [s.lower() for s in (resume.get('skills', []) or [])]
                    print(f"    {i}. {resume['first_name']} {resume['last_name']} (Score: {score:.3f})")
                    print(f"       Skills match: {'✓' if skills_match else '✗'}")
    
    async def _test_role_searches(self, db: AsyncSession):
        """Test role-based searches."""
        print("\n\n👔 ROLE-BASED SEARCHES")
        print("-" * 50)
        
        role_queries = [
            "software engineer",
            "senior developer",
            "data scientist",
            "devops engineer",
            "full stack developer",
            "frontend developer",
            "machine learning engineer",
            "technical lead"
        ]
        
        for query in role_queries:
            start_time = time.time()
            results = await search_service.search_resumes(db, query, self.user.id, limit=10)
            elapsed = time.time() - start_time
            
            self.results["role_searches"].append({
                "query": query,
                "count": len(results),
                "time": elapsed,
                "top_scores": [score for _, score in results[:3]]
            })
            
            print(f"\n  Query: '{query}'")
            print(f"  Found: {len(results)} results in {elapsed:.3f}s")
            
            if results:
                print("  Top 3 matches:")
                for i, (resume, score) in enumerate(results[:3], 1):
                    print(f"    {i}. {resume['first_name']} {resume['last_name']} - {resume.get('current_title', 'N/A')}")
                    print(f"       Score: {score:.3f}")
    
    async def _test_location_searches(self, db: AsyncSession):
        """Test location-based searches."""
        print("\n\n📍 LOCATION-BASED SEARCHES")
        print("-" * 50)
        
        location_queries = [
            "San Francisco",
            "New York",
            "London",
            "Bangalore",
            "remote"
        ]
        
        for query in location_queries:
            start_time = time.time()
            results = await search_service.search_resumes(db, query, self.user.id, limit=10)
            elapsed = time.time() - start_time
            
            self.results["location_searches"].append({
                "query": query,
                "count": len(results),
                "time": elapsed
            })
            
            print(f"\n  Query: '{query}'")
            print(f"  Found: {len(results)} results in {elapsed:.3f}s")
            
            if results[:3]:
                print("  Locations found:")
                for resume, _ in results[:3]:
                    print(f"    - {resume.get('location', 'N/A')}")
    
    async def _test_complex_searches(self, db: AsyncSession):
        """Test complex multi-criteria searches."""
        print("\n\n🔍 COMPLEX SEARCHES")
        print("-" * 50)
        
        complex_queries = [
            "senior python developer with aws experience",
            "react developer in San Francisco",
            "machine learning engineer with tensorflow and pytorch",
            "full stack developer javascript python",
            "devops engineer kubernetes docker aws",
            "data scientist with 5+ years experience"
        ]
        
        for query in complex_queries:
            start_time = time.time()
            results = await search_service.search_resumes(db, query, self.user.id, limit=10)
            elapsed = time.time() - start_time
            
            self.results["complex_searches"].append({
                "query": query,
                "count": len(results),
                "time": elapsed,
                "avg_score": mean([score for _, score in results]) if results else 0
            })
            
            print(f"\n  Query: '{query}'")
            print(f"  Found: {len(results)} results in {elapsed:.3f}s")
            
            if results:
                top_result = results[0]
                resume, score = top_result
                print(f"  Best match: {resume['first_name']} {resume['last_name']} (Score: {score:.3f})")
                print(f"  Title: {resume.get('current_title', 'N/A')}")
                print(f"  Skills: {', '.join(resume.get('skills', [])[:5])}...")
    
    async def _test_performance(self, db: AsyncSession):
        """Test search performance with various query types."""
        print("\n\n⚡ PERFORMANCE TESTING")
        print("-" * 50)
        
        # Test different query lengths
        test_queries = [
            ("Single word", "python"),
            ("Two words", "python developer"),
            ("Three words", "senior python developer"),
            ("Long query", "experienced software engineer with expertise in python django and react"),
            ("Very specific", "machine learning engineer with tensorflow pytorch nlp computer vision")
        ]
        
        for test_name, query in test_queries:
            # Run 5 times and average
            times = []
            for _ in range(5):
                start_time = time.time()
                results = await search_service.search_resumes(db, query, self.user.id, limit=20)
                elapsed = time.time() - start_time
                times.append(elapsed)
            
            avg_time = mean(times)
            self.results["performance"].append({
                "test": test_name,
                "query": query,
                "avg_time": avg_time,
                "min_time": min(times),
                "max_time": max(times)
            })
            
            print(f"\n  {test_name}: '{query}'")
            print(f"  Average time: {avg_time:.3f}s (min: {min(times):.3f}s, max: {max(times):.3f}s)")
    
    async def _analyze_results(self):
        """Analyze and display test results."""
        print("\n\n📈 ANALYSIS & SUMMARY")
        print("="*70)
        
        # Performance summary
        all_times = []
        for category in ["skill_searches", "role_searches", "location_searches", "complex_searches"]:
            for result in self.results[category]:
                all_times.append(result["time"])
        
        if all_times:
            print("\n⏱️  Performance Summary:")
            print(f"  Average search time: {mean(all_times):.3f}s")
            print(f"  Median search time: {median(all_times):.3f}s")
            print(f"  Fastest search: {min(all_times):.3f}s")
            print(f"  Slowest search: {max(all_times):.3f}s")
        
        # Relevance summary
        print("\n🎯 Relevance Summary:")
        
        # Skill search accuracy
        skill_results = self.results["skill_searches"]
        successful_skill_searches = sum(1 for r in skill_results if r["count"] > 0)
        print(f"  Skill searches: {successful_skill_searches}/{len(skill_results)} returned results")
        
        # Average scores by category
        for category, name in [
            ("skill_searches", "Skill searches"),
            ("role_searches", "Role searches"),
            ("complex_searches", "Complex searches")
        ]:
            scores = []
            for result in self.results[category]:
                if "top_scores" in result:
                    scores.extend(result["top_scores"])
                elif "avg_score" in result and result["avg_score"] > 0:
                    scores.append(result["avg_score"])
            
            if scores:
                print(f"  {name} avg score: {mean(scores):.3f}")
        
        # Search coverage
        print("\n📊 Search Coverage:")
        total_searches = sum(len(self.results[cat]) for cat in self.results if cat != "performance")
        searches_with_results = sum(
            1 for cat in self.results if cat != "performance"
            for r in self.results[cat] if r.get("count", 0) > 0
        )
        print(f"  Total searches: {total_searches}")
        print(f"  Searches with results: {searches_with_results} ({searches_with_results/total_searches*100:.1f}%)")
        
        print("\n✅ Vector search testing complete!")


async def main():
    """Run the vector search tests."""
    tester = VectorSearchTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())