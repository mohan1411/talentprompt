#!/usr/bin/env python3
"""Check if the backend has the latest code."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("Checking backend code versions...")
print("="*60)

# Check query_parser
try:
    from app.services.query_parser import query_parser
    import inspect
    
    # Get the parse_query method source
    source = inspect.getsource(query_parser.parse_query)
    
    print("1. Checking query_parser.parse_query:")
    if "original_query_lower" in source:
        print("   ✅ Has latest fix (original_query_lower)")
    else:
        print("   ❌ Missing latest fix")
    
    if "fuzzy_matcher.correct_query" in source:
        print("   ✅ Has typo correction")
    else:
        print("   ❌ Missing typo correction")
        
except Exception as e:
    print(f"   ❌ Error checking query_parser: {e}")

# Check fuzzy_matcher
try:
    from app.services.fuzzy_matcher import fuzzy_matcher
    
    print("\n2. Checking fuzzy_matcher:")
    print(f"   Threshold: {fuzzy_matcher.threshold}")
    print(f"   Has 'pythonn' in corrections: {'pythonn' in fuzzy_matcher.typo_corrections}")
    
except Exception as e:
    print(f"   ❌ Error checking fuzzy_matcher: {e}")

# Check gpt4_query_analyzer
try:
    from app.services.gpt4_query_analyzer import gpt4_analyzer
    import inspect
    
    merge_source = inspect.getsource(gpt4_analyzer._merge_analyses)
    
    print("\n3. Checking gpt4_query_analyzer._merge_analyses:")
    if "corrected_query" in merge_source:
        print("   ✅ Preserves corrected_query")
    else:
        print("   ❌ Doesn't preserve corrected_query")
        
except Exception as e:
    print(f"   ❌ Error checking gpt4_analyzer: {e}")

# Check the API endpoint
try:
    from app.api.v1.endpoints.search_progressive import analyze_query
    import inspect
    
    source = inspect.getsource(analyze_query)
    
    print("\n4. Checking analyze_query endpoint:")
    if "gpt4_analyzer.analyze_query" in source:
        print("   ✅ Uses GPT analyzer")
    else:
        print("   ❌ Doesn't use GPT analyzer")
        
except Exception as e:
    print(f"   ❌ Error checking API endpoint: {e}")

print("\n" + "="*60)
print("If any checks show ❌, the backend is not running the latest code.")