#!/usr/bin/env python3
"""Test if imports work correctly."""

print("Testing imports...")

try:
    from app.services.query_parser import query_parser
    print("✅ query_parser imported")
    
    # Test it
    result = query_parser.parse_query("Pythonn Developer")
    print(f"✅ parse_query works: corrected_query = {result.get('corrected_query')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()