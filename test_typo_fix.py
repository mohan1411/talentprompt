#!/usr/bin/env python3
"""Test script to verify typo correction and skill mapping is working"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.ai_typo_corrector import ai_typo_corrector
from app.services.async_query_parser import async_query_parser
from app.services.gpt4_query_analyzer import gpt4_analyzer
from app.services.progressive_search import progressive_search

async def test_typo_correction():
    """Test the typo correction flow"""
    
    print("=== Testing Typo Correction Flow ===\n")
    
    # Test 1: AI Typo Corrector
    print("1. Testing AI Typo Corrector:")
    typo_result = await ai_typo_corrector.correct_query('ams developer')
    print(f"   Original: {typo_result['original']}")
    print(f"   Corrected: {typo_result['corrected']}")
    print(f"   Has corrections: {typo_result['has_corrections']}")
    print(f"   Method: {typo_result['method']}")
    print()
    
    # Test 2: Async Query Parser
    print("2. Testing Async Query Parser:")
    parsed = await async_query_parser.parse_query_async('ams developer')
    print(f"   Original query: {parsed['original_query']}")
    print(f"   Corrected query: {parsed.get('corrected_query')}")
    print(f"   Skills extracted: {parsed['skills']}")
    print()
    
    # Test 3: GPT4 Analyzer Enhancement
    print("3. Testing GPT4 Analyzer Enhancement:")
    enhanced = gpt4_analyzer._enhance_basic_parse(parsed)
    print(f"   Primary skills: {enhanced.get('primary_skills')}")
    print(f"   Secondary skills: {enhanced.get('secondary_skills')}")
    print(f"   Implied skills: {enhanced.get('implied_skills')}")
    print()
    
    # Test 4: Test with correctly spelled skill
    print("4. Testing with correctly spelled 'javascript developer':")
    parsed_js = await async_query_parser.parse_query_async('javascript developer')
    enhanced_js = gpt4_analyzer._enhance_basic_parse(parsed_js)
    print(f"   Primary skills: {enhanced_js.get('primary_skills')}")
    print(f"   Secondary skills: {enhanced_js.get('secondary_skills')}")
    print()
    
    # Test 5: Test other common typos
    print("5. Testing other typos:")
    test_queries = [
        'pythonn developer',
        'javscript engineer', 
        'kuberentes admin'
    ]
    
    for query in test_queries:
        typo_result = await ai_typo_corrector.correct_query(query)
        parsed = await async_query_parser.parse_query_async(query)
        enhanced = gpt4_analyzer._enhance_basic_parse(parsed)
        print(f"   '{query}' -> '{typo_result['corrected']}' -> Secondary: {enhanced.get('secondary_skills', [])[:3]}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_typo_correction())