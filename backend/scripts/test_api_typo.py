#!/usr/bin/env python3
"""Test typo correction via API."""

import requests
import json

# Test the analyze-query endpoint
query = "Pythonn Developer"
token = input("Enter your access token: ").strip()

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

url = f"http://localhost:8001/api/v1/search/analyze-query?query={query}"

print(f"Testing API with query: '{query}'")
print(f"URL: {url}")
print("="*60)

try:
    response = requests.post(url, headers=headers, json={})
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\nFull response:")
        print(json.dumps(data, indent=2))
        
        analysis = data.get('analysis', {})
        print(f"\nAnalysis contains corrected_query: {'corrected_query' in analysis}")
        print(f"corrected_query value: {analysis.get('corrected_query')}")
        print(f"original_query value: {analysis.get('original_query')}")
        
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")