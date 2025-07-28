#!/usr/bin/env python3
"""Test query parser directly to see if corrected_query is generated."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up logging to see all debug messages
import logging
logging.basicConfig(level=logging.INFO)

from app.services.query_parser import query_parser

# Test the parser directly
test_query = "Pythonn Developer"
print(f"Testing query parser with: '{test_query}'")
print("="*60)

result = query_parser.parse_query(test_query)

print("\nParser result:")
for key, value in result.items():
    print(f"  {key}: {value}")

print(f"\nSpecifically checking corrected_query:")
print(f"  corrected_query exists: {'corrected_query' in result}")
print(f"  corrected_query value: {result.get('corrected_query')}")
print(f"  original_query: {result.get('original_query')}")

# Also test the correction directly
from app.services.fuzzy_matcher import fuzzy_matcher
query_lower = test_query.lower()
corrected = fuzzy_matcher.correct_query(query_lower)
print(f"\nDirect fuzzy_matcher test:")
print(f"  Input: '{query_lower}'")
print(f"  Output: '{corrected}'")
print(f"  Are they different? {corrected != query_lower}")