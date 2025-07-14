#!/usr/bin/env python3
"""Test the search API directly."""

import requests
import json
from typing import Dict, Any

API_URL = "http://localhost:8001"


def test_search(query: str, token: str = None) -> Dict[str, Any]:
    """Test the search endpoint."""
    
    headers = {
        "Content-Type": "application/json"
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    payload = {
        "query": query,
        "limit": 10
    }
    
    response = requests.post(
        f"{API_URL}/api/v1/search/",
        headers=headers,
        json=payload
    )
    
    return response


def login_and_get_token() -> str:
    """Login and get access token."""
    
    # Try to login with test credentials
    login_data = {
        "username": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(
        f"{API_URL}/api/v1/auth/login",
        data=login_data
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code}")
        print(response.json())
        return None


def main():
    """Main test function."""
    
    print("Testing Product Manager Search\n")
    print("=" * 60)
    
    # First, try to login
    print("\n1. Attempting to login...")
    token = login_and_get_token()
    
    if not token:
        print("\nTrying without authentication...")
        token = None
    else:
        print("   Login successful!")
    
    # Test the search
    print("\n2. Searching for 'product manager'...")
    response = test_search("product manager", token)
    
    print(f"\n   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json()
        print(f"   Found {len(results)} results:")
        print("\n" + "-" * 60)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['first_name']} {result['last_name']}")
            print(f"   Current Title: {result.get('current_title', 'N/A')}")
            print(f"   Score: {result.get('score', 'N/A')}")
            print(f"   Years Experience: {result.get('years_experience', 'N/A')}")
            print(f"   Location: {result.get('location', 'N/A')}")
            
            skills = result.get('skills', [])
            if skills:
                print(f"   Skills: {', '.join(skills[:5])}" + (" ..." if len(skills) > 5 else ""))
            
            if result.get('highlights'):
                print(f"   Highlights: {result['highlights'][0][:100]}..." if result['highlights'][0] else "")
    else:
        print(f"\n   Error: {response.text}")
    
    # Also test with a developer query for comparison
    print("\n\n3. Searching for 'python developer' (for comparison)...")
    response = test_search("python developer", token)
    
    if response.status_code == 200:
        results = response.json()
        print(f"   Found {len(results)} results")
        if results:
            print(f"   Top result: {results[0]['first_name']} {results[0]['last_name']} - {results[0].get('current_title', 'N/A')} (Score: {results[0].get('score', 'N/A')})")


if __name__ == "__main__":
    main()