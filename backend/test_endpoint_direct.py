#!/usr/bin/env python3
"""Test the endpoint directly to debug the issue."""

import requests
import json
import sys

# Get token
token = input("Enter your access token: ").strip()
if not token:
    print("Token required!")
    sys.exit(1)

# Test URL
url = "http://localhost:8001/api/v1/search/analyze-query?query=Pythonn%20Developer"

print(f"\nTesting: {url}")
print("="*60)

# Make request
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, headers=headers, json={})
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\nFull response:")
        print(json.dumps(data, indent=2))
        
        # Check specifically for corrected_query
        analysis = data.get("analysis", {})
        print(f"\n✓ Has corrected_query: {'corrected_query' in analysis}")
        print(f"✓ corrected_query value: {analysis.get('corrected_query')}")
        
        # Let's also check what keys are in analysis
        print(f"\n✓ Keys in analysis: {list(analysis.keys())}")
        
    else:
        print(f"\nError: {response.text}")
        
except Exception as e:
    print(f"\nError: {e}")

# Also test if the backend is receiving the print statements
print("\n" + "="*60)
print("Check your backend console - you should see:")
print("- [ENDPOINT] analyze_query called with: 'Pythonn Developer'")
print("- [DEBUG] QueryParser.parse_query called with: 'Pythonn Developer'")
print("- Various logging messages about corrected_query")