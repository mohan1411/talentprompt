#!/usr/bin/env python3
"""Test typo correction in search queries."""

from app.services.fuzzy_matcher import fuzzy_matcher
from app.services.query_parser import query_parser

# Test cases
test_queries = [
    "Pythonn Developer",
    "Javscript Engineer",
    "Reactt Developer",
    "Kubernets Expert",
    "Dokcer and Kubenetes",
    "Senior Pythoon Developer with AWS",
    "Nodjs Backend Developer",
    "Tyepscript React Developer"
]

print("Testing Typo Correction")
print("="*60)

# Test fuzzy matcher directly
print("\n1. Fuzzy Matcher Corrections:")
for query in test_queries:
    corrected = fuzzy_matcher.correct_query(query.lower())
    if corrected != query.lower():
        print(f"   '{query}' -> '{corrected}'")
    else:
        print(f"   '{query}' (no correction)")

# Test through query parser
print("\n2. Query Parser with Typo Correction:")
for query in test_queries:
    result = query_parser.parse_query(query)
    print(f"\n   Query: '{query}'")
    if result.get('corrected_query'):
        print(f"   Corrected: '{result['corrected_query']}'")
    print(f"   Skills found: {result['skills']}")

# Test similarity scores
print("\n3. Similarity Scores:")
typo_tests = [
    ("pythonn", "python"),
    ("javscript", "javascript"),
    ("dokcer", "docker"),
    ("reactt", "react"),
    ("nodjs", "node")
]

for typo, correct in typo_tests:
    score = fuzzy_matcher.similarity_score(typo, correct)
    print(f"   '{typo}' vs '{correct}': {score:.2f}")