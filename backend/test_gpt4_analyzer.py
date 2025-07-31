#!/usr/bin/env python3
"""Test GPT4 analyzer directly to debug secondary skills."""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, '/mnt/d/Projects/AI/BusinessIdeas/SmallBusiness/TalentPrompt/backend')

# Set up minimal environment
os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost/db'
os.environ['SECRET_KEY'] = 'test'

from app.services.gpt4_query_analyzer import GPT4QueryAnalyzer

async def test_analyzer():
    """Test the GPT4 analyzer with various queries."""
    
    analyzer = GPT4QueryAnalyzer()
    
    test_queries = [
        "javascript developer",
        "python developer", 
        "senior python developer with aws",
        "react typescript engineer"
    ]
    
    print("Testing GPT4 Query Analyzer...")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: \"{query}\"")
        print("-" * 40)
        
        try:
            # Test the analyze_query method
            analysis = await analyzer.analyze_query(query)
            
            print(f"Primary Skills: {analysis.get('primary_skills', [])}")
            print(f"Secondary Skills: {analysis.get('secondary_skills', [])}")
            print(f"Implied Skills: {analysis.get('implied_skills', [])}")
            print(f"Experience Level: {analysis.get('experience_level', 'any')}")
            print(f"Role Type: {analysis.get('role_type', 'any')}")
            
            # Test suggestions
            suggestions = analyzer.get_search_suggestions(analysis)
            print(f"Suggestions: {suggestions}")
            
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_analyzer())