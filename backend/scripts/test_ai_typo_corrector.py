#!/usr/bin/env python3
"""Test script for AI typo corrector."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.ai_typo_corrector import ai_typo_corrector
from app.services.async_query_parser import async_query_parser


async def test_typo_corrections():
    """Test various typo corrections."""
    
    test_queries = [
        "Pythonn developer with AMS experience",
        "javscript and raect developer",
        "senior devops enginer with kuberentes",
        "looking for fulstack developer",
        "need someone with miscrosoft azure",
        "frontend developr with 5+ years",
        "backend engineer with dokcer and kubernets",
        "data scintist with pythn and tensorflow"
    ]
    
    print("Testing AI Typo Corrector\n" + "="*50)
    
    for query in test_queries:
        print(f"\nOriginal: {query}")
        
        # Test AI typo corrector directly
        result = await ai_typo_corrector.correct_query(query)
        print(f"Corrected: {result['corrected']}")
        
        if result['corrections']:
            print("Corrections:")
            for correction in result['corrections']:
                print(f"  - '{correction['from']}' → '{correction['to']}' (confidence: {correction['confidence']:.2f})")
        
        print(f"Overall confidence: {result['confidence']:.2f}")
        print(f"Method: {result['method']}")
    
    print("\n" + "="*50)
    print("Testing Async Query Parser with AI Corrections\n")
    
    # Test a complex query
    complex_query = "senoir Pythonn developr with AMS and kuberentes experiance"
    print(f"Complex query: {complex_query}")
    
    parsed = await async_query_parser.parse_query_async(complex_query)
    
    print(f"\nParsed Results:")
    print(f"  Original: {parsed['original_query']}")
    print(f"  Corrected: {parsed.get('corrected_query', 'No corrections')}")
    print(f"  Skills: {parsed['skills']}")
    print(f"  Primary skill: {parsed.get('primary_skill')}")
    print(f"  Seniority: {parsed.get('seniority')}")
    print(f"  Roles: {parsed.get('roles', [])}")
    
    if parsed.get('corrections'):
        print("\nCorrections applied:")
        for correction in parsed['corrections']:
            print(f"  - '{correction['from']}' → '{correction['to']}'")


async def test_feedback_learning():
    """Test learning from user feedback."""
    print("\n" + "="*50)
    print("Testing Feedback Learning\n")
    
    # Simulate user correction
    original = "miscrosoft teams"
    user_correction = "Microsoft Teams"
    
    print(f"User corrected: '{original}' → '{user_correction}'")
    await ai_typo_corrector.learn_from_feedback(original, user_correction)
    print("Feedback stored for future corrections")


if __name__ == "__main__":
    asyncio.run(test_typo_corrections())
    asyncio.run(test_feedback_learning())