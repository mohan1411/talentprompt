#!/usr/bin/env python3
"""Test backend endpoints directly."""

import requests
import json

print("="*60)
print("BACKEND API TEST")
print("="*60)

# Test endpoints
base_url = "http://localhost:8001"

# 1. Test health endpoint
print("\n1. Testing health endpoint...")
try:
    response = requests.get(f"{base_url}/api/v1/health/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Test root endpoint
print("\n2. Testing root endpoint...")
try:
    response = requests.get(f"{base_url}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Test docs
print("\n3. Testing docs endpoint...")
try:
    response = requests.get(f"{base_url}/docs")
    print(f"   Status: {response.status_code}")
    print(f"   Docs available: {'swagger' in response.text.lower()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Test CORS preflight
print("\n4. Testing CORS preflight...")
try:
    response = requests.options(
        f"{base_url}/api/v1/health/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization"
        }
    )
    print(f"   Status: {response.status_code}")
    print("   CORS Headers:")
    for header, value in response.headers.items():
        if "access-control" in header.lower():
            print(f"   - {header}: {value}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 5. Test with token (if available)
print("\n5. Testing with token...")
token = input("Paste token (or press Enter to skip): ").strip()

if token:
    try:
        response = requests.get(
            f"{base_url}/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            user = response.json()
            print(f"   ✅ User: {user.get('email')}")
            
            # Test resume endpoint
            response = requests.get(
                f"{base_url}/api/v1/resumes/",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"\n   Resume API Status: {response.status_code}")
            if response.status_code == 200:
                resumes = response.json()
                print(f"   ✅ Found {len(resumes)} resumes")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("\nIf the Python script works but the browser doesn't:")
print("1. It's likely a CORS or browser security issue")
print("2. Try opening http://localhost:8001/docs in your browser")
print("3. Make sure no browser extensions are blocking requests")
print("4. Try using an incognito window")
print("\nTo fix CORS, ensure backend is started with proper settings:")
print("  export BACKEND_CORS_ORIGINS='http://localhost:3000,http://localhost:8000'")
print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8001")