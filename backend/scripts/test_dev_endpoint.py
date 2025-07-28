#!/usr/bin/env python3
"""Test if the dev endpoint is accessible."""

import requests
import json

# Test the endpoint
url = "http://localhost:8001/api/v1/auth/dev/generate-oauth-token?email=promtitude@gmail.com"

print("Testing dev endpoint...")
print(f"URL: {url}")

try:
    # First test if backend is running
    health_url = "http://localhost:8001/api/v1/health/"
    health_response = requests.get(health_url)
    print(f"\nHealth check: {health_response.status_code}")
    
    # Now test the dev endpoint
    response = requests.post(url)
    print(f"\nDev endpoint response: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nSuccess! Token generated.")
        print(f"Token (first 50 chars): {data['access_token'][:50]}...")
    else:
        print(f"\nError response: {response.text}")
        
        # Try to get more info
        print("\nTrying to list all routes...")
        openapi_url = "http://localhost:8001/openapi.json"
        openapi_response = requests.get(openapi_url)
        if openapi_response.status_code == 200:
            routes = openapi_response.json()
            auth_routes = [path for path in routes['paths'].keys() if 'auth' in path]
            print("Auth-related routes:")
            for route in sorted(auth_routes):
                print(f"  {route}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ Cannot connect to backend at http://localhost:8001")
    print("Make sure your backend is running with:")
    print("  cd backend")
    print("  uvicorn app.main:app --reload --port 8001")
except Exception as e:
    print(f"\n❌ Error: {e}")