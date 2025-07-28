#!/usr/bin/env python3
"""Test backend directly without going through uvicorn."""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_analyze_query():
    """Test the analyze_query endpoint directly."""
    
    # Import after path is set
    from app.services.gpt4_query_analyzer import gpt4_analyzer
    from app.services.query_parser import query_parser
    
    query = "Pythonn Developer"
    
    print("Testing backend components directly...")
    print("="*60)
    
    # Test query parser
    print(f"\n1. Testing query_parser with '{query}':")
    parsed = query_parser.parse_query(query)
    print(f"   corrected_query: {parsed.get('corrected_query')}")
    print(f"   original_query: {parsed.get('original_query')}")
    
    # Test GPT analyzer
    print(f"\n2. Testing gpt4_analyzer with '{query}':")
    analysis = await gpt4_analyzer.analyze_query(query, {})
    print(f"   corrected_query in analysis: {analysis.get('corrected_query')}")
    print(f"   original_query in analysis: {analysis.get('original_query')}")
    
    # Check if corrected_query is being preserved
    print(f"\n3. Summary:")
    print(f"   Query parser generates corrected_query: {'corrected_query' in parsed}")
    print(f"   GPT analyzer preserves corrected_query: {'corrected_query' in analysis}")
    
    if 'corrected_query' not in analysis:
        print("\n⚠️  corrected_query is being lost in the GPT analyzer!")

if __name__ == "__main__":
    asyncio.run(test_analyze_query())