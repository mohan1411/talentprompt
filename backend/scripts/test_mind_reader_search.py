"""Test script for the Mind Reader enhanced vector search."""

import asyncio
import json
import time
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import async_session
from app.services.search import search_service
from app.services.gpt4_query_analyzer import gpt4_analyzer
from app.models.user import User
from sqlalchemy import select


async def test_progressive_search(user_email: str = "admin@promtitude.com"):
    """Test the progressive search functionality."""
    print("\n" + "="*80)
    print("MIND READER SEARCH TEST - Progressive Search with GPT-4.1-mini")
    print("="*80)
    
    async with async_session() as db:
        # Get user
        stmt = select(User).where(User.email == user_email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User {user_email} not found!")
            return
        
        # Test queries
        test_queries = [
            "Senior Python Developer with AWS experience",
            "Full-stack engineer who can mentor juniors",
            "React developer with TypeScript and testing experience",
            "DevOps engineer comfortable with Kubernetes",
            "Find me a unicorn developer",  # Complex query
            "Machine learning engineer with production experience"
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"QUERY: '{query}'")
            print(f"{'='*60}")
            
            # 1. Analyze query with GPT-4.1-mini
            print("\n1. QUERY ANALYSIS (GPT-4.1-mini):")
            print("-" * 40)
            
            analysis = await search_service.analyze_query_advanced(query)
            
            # Pretty print key analysis results
            print(f"Primary Skills: {analysis.get('primary_skills', [])}")
            print(f"Secondary Skills: {analysis.get('secondary_skills', [])}")
            print(f"Implied Skills: {analysis.get('implied_skills', [])}")
            print(f"Experience Level: {analysis.get('experience_level', 'any')}")
            print(f"Role Type: {analysis.get('role_type', 'any')}")
            print(f"Search Intent: {analysis.get('search_intent', 'unknown')}")
            print(f"Query Quality: {analysis.get('query_quality', 'unknown')}")
            
            if analysis.get('interpretation_notes'):
                print(f"\nInterpretation: {analysis['interpretation_notes']}")
            
            # Get query suggestions
            suggestions = gpt4_analyzer.get_search_suggestions(analysis)
            if suggestions:
                print(f"\nSuggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion}")
            
            # 2. Progressive Search
            print(f"\n2. PROGRESSIVE SEARCH RESULTS:")
            print("-" * 40)
            
            stage_count = 0
            final_results = None
            
            async for stage_result in search_service.search_resumes_progressive(
                db=db,
                query=query,
                user_id=user.id,
                limit=5
            ):
                stage_count += 1
                stage = stage_result["stage"]
                timing = stage_result["timing_ms"]
                count = stage_result["count"]
                
                print(f"\nStage {stage_result['stage_number']}: {stage.upper()} ({timing}ms)")
                print(f"Found {count} results")
                
                if count > 0 and stage_result["is_final"]:
                    final_results = stage_result["results"]
                    
                    # Show top 3 results
                    for i, (resume, score) in enumerate(final_results[:3], 1):
                        print(f"\n  {i}. {resume['first_name']} {resume['last_name']} - {resume.get('current_title', 'N/A')}")
                        print(f"     Score: {score:.3f}")
                        
                        if resume.get('match_explanation'):
                            print(f"     Why: {resume['match_explanation']}")
                        
                        if resume.get('skill_analysis'):
                            analysis = resume['skill_analysis']
                            if analysis.get('matched'):
                                print(f"     Matched Skills: {', '.join(analysis['matched'])}")
                            if analysis.get('missing'):
                                print(f"     Missing Skills: {', '.join(analysis['missing'])}")
                            if analysis.get('additional'):
                                print(f"     Bonus Skills: {', '.join(analysis['additional'])}")
            
            # Quality assessment
            if stage_result:
                quality_score = stage_result.get('search_quality_score', 0)
                print(f"\nSearch Quality Score: {quality_score:.2f}/1.0")
            
            # Wait before next query
            await asyncio.sleep(1)


async def test_query_expansions():
    """Test query expansion capabilities."""
    print("\n" + "="*80)
    print("QUERY EXPANSION TEST")
    print("="*80)
    
    test_queries = [
        "Python developer",
        "Senior engineer",
        "AWS architect",
        "Full-stack",
        "ML engineer"
    ]
    
    for query in test_queries:
        print(f"\nOriginal: '{query}'")
        
        # Analyze and expand
        analysis = await gpt4_analyzer.analyze_query(query)
        expansions = await gpt4_analyzer.expand_query(query, analysis)
        
        print("Expansions:")
        for i, expansion in enumerate(expansions, 1):
            print(f"  {i}. {expansion}")


async def test_cost_analysis():
    """Analyze estimated costs for the enhanced search."""
    print("\n" + "="*80)
    print("COST ANALYSIS")
    print("="*80)
    
    # Estimate monthly usage
    daily_searches = 100
    avg_resumes_per_user = 500
    new_resumes_daily = 10
    
    # Cost calculations
    print("\nEstimated Monthly Usage:")
    print(f"- Daily searches: {daily_searches}")
    print(f"- Monthly searches: {daily_searches * 30}")
    print(f"- New resumes/day: {new_resumes_daily}")
    print(f"- Monthly new resumes: {new_resumes_daily * 30}")
    
    print("\nCost Breakdown:")
    
    # Embeddings
    embedding_cost_per_1k_tokens = 0.00002  # text-embedding-3-small
    avg_tokens_per_resume = 500
    monthly_embedding_cost = (new_resumes_daily * 30 * avg_tokens_per_resume / 1000) * embedding_cost_per_1k_tokens
    print(f"- Embeddings: ${monthly_embedding_cost:.2f}")
    
    # GPT-4.1-mini for analysis
    gpt4_mini_input_cost = 0.00015  # per 1k tokens
    gpt4_mini_output_cost = 0.0006   # per 1k tokens
    avg_query_tokens = 100
    avg_response_tokens = 200
    
    monthly_gpt4_cost = daily_searches * 30 * (
        (avg_query_tokens / 1000 * gpt4_mini_input_cost) +
        (avg_response_tokens / 1000 * gpt4_mini_output_cost)
    )
    print(f"- GPT-4.1-mini: ${monthly_gpt4_cost:.2f}")
    
    # Redis (free tier usually sufficient for <500MB)
    redis_cost = 5.0  # Assume $5/month for Redis Cloud 512MB
    print(f"- Redis Cloud: ${redis_cost:.2f}")
    
    # Total
    total_cost = monthly_embedding_cost + monthly_gpt4_cost + redis_cost
    print(f"\nTOTAL ESTIMATED COST: ${total_cost:.2f}/month")
    print(f"Budget remaining: ${20 - total_cost:.2f}/month")


async def main():
    """Run all tests."""
    # Test progressive search
    await test_progressive_search()
    
    # Test query expansions
    await test_query_expansions()
    
    # Cost analysis
    await test_cost_analysis()


if __name__ == "__main__":
    asyncio.run(main())