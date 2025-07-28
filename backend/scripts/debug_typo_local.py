#!/usr/bin/env python3
"""Debug typo correction locally."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.fuzzy_matcher import fuzzy_matcher
from app.services.query_parser import query_parser

# Test query
test_query = "Pythonn Developer"

print(f"Testing query: '{test_query}'")
print("="*60)

# Test fuzzy matcher directly
print("\n1. Testing fuzzy_matcher.correct_query():")
corrected = fuzzy_matcher.correct_query(test_query.lower())
print(f"   Input: '{test_query.lower()}'")
print(f"   Output: '{corrected}'")

# Test suggest_corrections
print("\n2. Testing fuzzy_matcher.suggest_corrections():")
words = test_query.split()
suggestions = fuzzy_matcher.suggest_corrections(words)
print(f"   Input words: {words}")
print(f"   Suggestions: {suggestions}")

# Test similarity score
print("\n3. Testing similarity scores:")
print(f"   'pythonn' vs 'python': {fuzzy_matcher.similarity_score('pythonn', 'python')}")
print(f"   Threshold: {fuzzy_matcher.threshold}")

# Test fuzzy match
print("\n4. Testing fuzzy_match():")
matches = fuzzy_matcher.fuzzy_match('pythonn', ['python', 'java', 'javascript'])
print(f"   Matches: {matches}")

# Test query parser
print("\n5. Testing query_parser.parse_query():")
parsed = query_parser.parse_query(test_query)
print(f"   Parsed result:")
print(f"   - original_query: {parsed.get('original_query')}")
print(f"   - corrected_query: {parsed.get('corrected_query')}")
print(f"   - skills: {parsed.get('skills')}")

# Check if pythonn is in typo_corrections
print("\n6. Checking typo_corrections mapping:")
print(f"   'pythonn' in typo_corrections: {'pythonn' in fuzzy_matcher.typo_corrections}")
if 'pythonn' in fuzzy_matcher.typo_corrections:
    print(f"   Maps to: {fuzzy_matcher.typo_corrections['pythonn']}")