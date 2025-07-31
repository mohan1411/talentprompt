#!/usr/bin/env python3
"""Test query analysis directly."""

import asyncio
import sys
sys.path.append('/mnt/d/Projects/AI/BusinessIdeas/SmallBusiness/TalentPrompt/backend')

from app.services.gpt4_query_analyzer import gpt4_analyzer

async def test_query_analysis():
    """Test the query analyzer directly."""
    
    test_queries = [
        "Python Developers with AWS",
        "Senior Django developer with EC2 experience",
        "React and TypeScript frontend engineer"
    ]
    
    print("Testing GPT4 Query Analyzer...")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: \"{query}\"")
        print("-" * 40)
        
        try:
            analysis = await gpt4_analyzer.analyze_query(query)
            print(f"  Primary Skills: {analysis.get('primary_skills', [])}")
            print(f"  Secondary Skills: {analysis.get('secondary_skills', [])}")
            print(f"  Implied Skills: {analysis.get('implied_skills', [])}")
            print(f"  Experience Level: {analysis.get('experience_level', 'any')}")
            print(f"  Role Type: {analysis.get('role_type', 'any')}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_query_analysis())