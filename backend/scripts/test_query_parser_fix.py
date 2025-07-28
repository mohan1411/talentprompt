#!/usr/bin/env python3
"""Test the query parser fix for the 'r' in 'Developer' bug."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.query_parser import query_parser


def test_query_parser():
    """Test various queries to ensure the parser works correctly."""
    test_cases = [
        ("Senior Python Developer with AWS", ["python", "aws"], "Should extract Python and AWS, not 'r'"),
        ("R Developer with Python", ["r", "python"], "Should extract R when it's a standalone word"),
        ("JavaScript React Developer", ["javascript", "react"], "Should extract JavaScript and React"),
        ("C++ Developer", ["c++"], "Should extract C++"),
        ("Go Developer with Kubernetes", ["go", "kubernetes"], "Should extract Go and Kubernetes"),
        ("Developer with R and Python", ["r", "python"], "Should extract R when standalone"),
        ("Ruby on Rails Developer", ["ruby on rails"], "Should handle multi-word skills"),
        ("Machine Learning Engineer with TensorFlow", ["machine learning", "tensorflow"], "Should extract ML skills"),
        ("Full Stack Developer", [], "Should not extract any skills from generic terms"),
        ("iOS and Android Developer", ["ios", "android"], "Should extract mobile platforms")
    ]
    
    print("Testing Query Parser Fix")
    print("=" * 70)
    
    all_passed = True
    
    for query, expected_skills, description in test_cases:
        result = query_parser.parse_query(query)
        extracted_skills = result["skills"]
        
        # Check if extracted skills match expected
        if set(extracted_skills) == set(expected_skills):
            print(f"✅ PASS: {query}")
            print(f"   {description}")
            print(f"   Extracted: {extracted_skills}")
        else:
            print(f"❌ FAIL: {query}")
            print(f"   {description}")
            print(f"   Expected: {expected_skills}")
            print(f"   Got: {extracted_skills}")
            all_passed = False
        print()
    
    print("=" * 70)
    
    # Test the specific bug case in detail
    print("\nDetailed test for 'Senior Python Developer with AWS':")
    result = query_parser.parse_query("Senior Python Developer with AWS")
    print(f"Skills extracted: {result['skills']}")
    print(f"Seniority: {result['seniority']}")
    print(f"Roles: {result['roles']}")
    print(f"Remaining terms: {result['remaining_terms']}")
    
    if 'r' in result['skills']:
        print("\n❌ BUG STILL EXISTS: 'r' is being extracted from 'Developer'")
        all_passed = False
    else:
        print("\n✅ BUG FIXED: 'r' is not being extracted from 'Developer'")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    
    return all_passed


if __name__ == "__main__":
    success = test_query_parser()
    sys.exit(0 if success else 1)