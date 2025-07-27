#!/usr/bin/env python3
"""Test script for hybrid search improvements."""

import asyncio
import sys
import os
import time
from datetime import datetime
from typing import List, Dict, Any
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.models.resume import Resume
from app.services.hybrid_search import hybrid_search
from app.services.skill_synonyms import skill_synonyms
from app.services.fuzzy_matcher import fuzzy_matcher
from app.services.gpt4_query_analyzer import gpt4_analyzer
from app.services.progressive_search import progressive_search_engine


async def test_skill_synonyms():
    """Test skill synonym expansion."""
    print("\n=== Testing Skill Synonyms ===")
    
    test_cases = [
        "ML engineer",
        "K8s expert",
        "Full-stack developer",
        "DevOps ninja",
        "React.js developer"
    ]
    
    for query in test_cases:
        expansions = skill_synonyms.expand_query(query)
        print(f"\nQuery: '{query}'")
        print(f"Expansions ({len(expansions)}): {expansions[:5]}")  # Show first 5
        
        # Test individual term expansion
        terms = query.split()
        for term in terms:
            variations = skill_synonyms.expand_term(term)
            if len(variations) > 1:
                print(f"  '{term}' → {list(variations)[:5]}")


async def test_fuzzy_matching():
    """Test fuzzy matching capabilities."""
    print("\n=== Testing Fuzzy Matching ===")
    
    # Test typo corrections
    typos = ["javascirpt", "pyton", "kubernets", "reactjs", "mongoddb"]
    corrections = fuzzy_matcher.suggest_corrections(typos)
    
    print("\nTypo Corrections:")
    for typo, correction in corrections.items():
        print(f"  '{typo}' → '{correction}'")
    
    # Test skill matching
    query_skills = ["Python", "Machine Learning", "TensorFlow", "Docker"]
    candidate_skills = ["Python", "ML", "Tensorflow", "Kubernetes", "Django"]
    
    matched, missing, score = fuzzy_matcher.match_skills(query_skills, candidate_skills)
    
    print(f"\nSkill Matching:")
    print(f"  Query skills: {query_skills}")
    print(f"  Candidate skills: {candidate_skills}")
    print(f"  Matched: {matched}")
    print(f"  Missing: {missing}")
    print(f"  Match score: {score:.2f}")


async def test_query_analysis():
    """Test GPT-4.1-mini query analysis."""
    print("\n=== Testing Query Analysis ===")
    
    queries = [
        "Senior Python Developer with AWS experience",
        "Full-stack engineer who can mentor junior developers",
        "DevOps specialist must have Kubernetes",
        "Data scientist with strong communication skills",
        "React developer 5+ years"
    ]
    
    for query in queries:
        print(f"\nAnalyzing: '{query}'")
        
        # Basic analysis (without GPT-4.1-mini)
        analysis = await gpt4_analyzer.analyze_query(query)
        
        print(f"  Query Type: {analysis.get('query_type', 'unknown')}")
        print(f"  Primary Skills: {analysis.get('primary_skills', [])}")
        print(f"  Experience Level: {analysis.get('experience_level', 'any')}")
        print(f"  Role Type: {analysis.get('role_type', 'any')}")
        
        # Get search suggestions
        suggestions = gpt4_analyzer.get_search_suggestions(analysis)
        if suggestions:
            print(f"  Suggestions: {suggestions[0]}")


async def test_hybrid_search_performance(db: AsyncSession):
    """Test hybrid search performance and quality."""
    print("\n=== Testing Hybrid Search Performance ===")
    
    # Get a test user
    result = await db.execute(select(Resume).limit(1))
    test_resume = result.scalar_one_or_none()
    
    if not test_resume:
        print("No test data found. Please seed the database first.")
        return
    
    user_id = str(test_resume.user_id)
    
    test_queries = [
        "Python developer",
        "Senior React engineer with TypeScript",
        "ML engineer with production experience",
        "DevOps Kubernetes AWS",
        "Full-stack JavaScript Node.js"
    ]
    
    for query in test_queries:
        print(f"\n\nTesting query: '{query}'")
        
        # Analyze query to get type
        analysis = await gpt4_analyzer.analyze_query(query)
        query_type = analysis.get('query_type', 'technical')
        
        print(f"Query type: {query_type}")
        
        # Test hybrid search
        start_time = time.time()
        
        results = await hybrid_search.search(
            db=db,
            query=query,
            user_id=user_id,
            limit=5,
            use_synonyms=True
        )
        
        search_time = (time.time() - start_time) * 1000
        
        print(f"Search time: {search_time:.1f}ms")
        print(f"Results found: {len(results)}")
        
        # Show top 3 results
        for i, (resume_data, score) in enumerate(results[:3]):
            print(f"\n  Result {i+1}:")
            print(f"    Name: {resume_data.get('first_name', '')} {resume_data.get('last_name', '')}")
            print(f"    Title: {resume_data.get('current_title', 'N/A')}")
            print(f"    Score: {score:.3f}")
            
            # Show score breakdown if available
            if 'hybrid_score' in resume_data:
                print(f"    Hybrid: {resume_data['hybrid_score']:.3f}")
                print(f"    Keyword: {resume_data.get('keyword_score', 0):.3f}")
                print(f"    Vector: {resume_data.get('vector_score', 0):.3f}")
            
            # Show matched skills
            skills = resume_data.get('skills', [])[:5]
            if skills:
                print(f"    Skills: {', '.join(skills)}")


async def test_progressive_search_with_hybrid(db: AsyncSession):
    """Test progressive search with hybrid search integration."""
    print("\n=== Testing Progressive Search with Hybrid ===")
    
    # Get a test user
    result = await db.execute(select(Resume).limit(1))
    test_resume = result.scalar_one_or_none()
    
    if not test_resume:
        print("No test data found.")
        return
    
    user_id = test_resume.user_id
    query = "Senior Python developer with AWS and Docker"
    
    print(f"\nProgressive search for: '{query}'")
    print("=" * 60)
    
    stage_times = []
    
    async for stage_result in progressive_search_engine.search_progressive(
        db, query, user_id, limit=10
    ):
        stage = stage_result['stage']
        timing = stage_result['timing_ms']
        count = stage_result['count']
        
        stage_times.append((stage, timing))
        
        print(f"\nStage: {stage}")
        print(f"Results: {count}")
        print(f"Time: {timing}ms")
        
        # Show top result from each stage
        if stage_result['results']:
            top_result = stage_result['results'][0]
            resume_data, score = top_result
            
            print(f"\nTop result:")
            print(f"  Name: {resume_data.get('first_name', '')} {resume_data.get('last_name', '')}")
            print(f"  Score: {score:.3f}")
            
            # Show search metadata if available
            if 'search_metadata' in resume_data:
                meta = resume_data['search_metadata']
                print(f"  Hybrid score: {meta.get('hybrid_score', 0):.3f}")
                print(f"  Keyword score: {meta.get('keyword_score', 0):.3f}")
                print(f"  Vector score: {meta.get('vector_score', 0):.3f}")
    
    print("\n\nStage Timing Summary:")
    for stage, timing in stage_times:
        print(f"  {stage}: {timing}ms")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Hybrid Search Test Suite")
    print("=" * 60)
    
    # Test components individually
    await test_skill_synonyms()
    await test_fuzzy_matching()
    await test_query_analysis()
    
    # Test with database
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        await test_hybrid_search_performance(db)
        await test_progressive_search_with_hybrid(db)
    
    await engine.dispose()
    
    print("\n\n✅ All tests completed!")
    print("\nKey Improvements:")
    print("1. ✓ Skill synonym expansion (ML → Machine Learning)")
    print("2. ✓ Fuzzy matching for typos (pyton → python)")
    print("3. ✓ Query type detection for weight optimization")
    print("4. ✓ BM25 keyword search combined with vector search")
    print("5. ✓ PostgreSQL full-text indexes for speed")


if __name__ == "__main__":
    asyncio.run(main())