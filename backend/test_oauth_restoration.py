#!/usr/bin/env python3
"""Test script to verify OAuth restoration."""

import requests
import json

def test_oauth_endpoints():
    """Test if OAuth endpoints are accessible."""
    base_url = "http://localhost:8001/api/v1"
    
    print("OAuth Restoration Test")
    print("=" * 60)
    
    # Test 1: Check if dev_oauth endpoint is available
    print("\n1. Testing dev_oauth endpoint...")
    try:
        response = requests.get(f"{base_url}/auth/dev/generate-oauth-token")
        if response.status_code == 405:  # Method not allowed means endpoint exists
            print("✅ dev_oauth endpoint is registered (POST method required)")
        elif response.status_code == 404:
            print("❌ dev_oauth endpoint not found - check ENVIRONMENT or ALLOW_DEV_ENDPOINTS")
        else:
            print(f"ℹ️  dev_oauth endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing dev_oauth: {e}")
    
    # Test 2: Check OAuth v1 endpoints
    print("\n2. Testing OAuth v1 endpoints...")
    oauth_v1_endpoints = [
        "/oauth/google/login",
        "/oauth/linkedin/login",
        "/oauth/google/callback",
        "/oauth/linkedin/callback"
    ]
    
    for endpoint in oauth_v1_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            if response.status_code in [400, 422, 501]:  # Expected errors for GET without params
                print(f"✅ {endpoint} - endpoint exists")
            elif response.status_code == 404:
                print(f"❌ {endpoint} - endpoint not found")
            else:
                print(f"ℹ️  {endpoint} - returned {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - error: {e}")
    
    # Test 3: Check OAuth v2 endpoint
    print("\n3. Testing OAuth v2 endpoint...")
    try:
        response = requests.post(f"{base_url}/oauth/v2/token", json={})
        if response.status_code == 422:  # Validation error means endpoint exists
            print("✅ /oauth/v2/token endpoint is registered")
        elif response.status_code == 404:
            print("❌ /oauth/v2/token endpoint not found")
        else:
            print(f"ℹ️  /oauth/v2/token returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing OAuth v2: {e}")
    
    # Test 4: Check if Google OAuth is configured
    print("\n4. Testing Google OAuth configuration...")
    try:
        response = requests.get(f"{base_url}/oauth/google/login")
        if response.status_code == 501:
            print("⚠️  Google OAuth not configured (missing GOOGLE_CLIENT_ID)")
        elif response.status_code == 200:
            data = response.json()
            print(f"✅ Google OAuth configured - auth URL available")
        else:
            print(f"ℹ️  Google OAuth returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking Google OAuth: {e}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("- OAuth endpoints have been added to the API router")
    print("- Dev OAuth endpoint requires ENVIRONMENT=development or ALLOW_DEV_ENDPOINTS=true")
    print("- Google/LinkedIn OAuth requires client credentials in .env file")
    print("\nTo use the dev OAuth helper:")
    print("1. Set ALLOW_DEV_ENDPOINTS=true in your .env file")
    print("2. Restart the backend")
    print("3. Run: python scripts/simple_oauth_helper.py")


if __name__ == "__main__":
    try:
        test_oauth_endpoints()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend at http://localhost:8001")
        print("Make sure your backend is running with:")
        print("cd backend && uvicorn app.main:app --reload --port 8001")