#!/usr/bin/env python3
"""Simple typo test."""

from difflib import SequenceMatcher

# Test similarity
str1 = "pythonn"
str2 = "python"

# Basic similarity
ratio = SequenceMatcher(None, str1, str2).ratio()
print(f"Similarity between '{str1}' and '{str2}': {ratio}")
print(f"Is {ratio} >= 0.8? {ratio >= 0.8}")

# Test with normalization
str1_norm = str1.lower().strip()
str2_norm = str2.lower().strip()
ratio_norm = SequenceMatcher(None, str1_norm, str2_norm).ratio()
print(f"\nAfter normalization:")
print(f"'{str1_norm}' vs '{str2_norm}': {ratio_norm}")

# Test the actual typo_corrections
print("\n" + "="*50)
print("Testing fuzzy_matcher setup:")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.fuzzy_matcher import fuzzy_matcher

print(f"\nIs 'pythonn' in common_replacements['python']?")
print(f"python typos: {fuzzy_matcher.common_replacements.get('python', [])}")
print(f"\nIs 'pythonn' in typo_corrections?")
print(f"'pythonn' -> {fuzzy_matcher.typo_corrections.get('pythonn', 'NOT FOUND')}")