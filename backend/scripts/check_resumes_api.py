#!/usr/bin/env python3
"""Check resumes via API."""

import requests
import json

print("="*60)
print("RESUME API CHECK")
print("="*60)

# Test different scenarios
base_url = "http://localhost:8001/api/v1"

# 1. First check if backend is running
try:
    health = requests.get(f"{base_url}/health/")
    print(f"✅ Backend is running: {health.status_code}")
except:
    print("❌ Backend is not running at http://localhost:8001")
    print("Start it with: cd backend && uvicorn app.main:app --reload --port 8001")
    exit(1)

# 2. Check resume endpoint without auth
print("\n1. Testing resume endpoint without auth:")
response = requests.get(f"{base_url}/resumes/")
print(f"   Status: {response.status_code}")
if response.status_code == 401:
    print("   ✅ Correctly requires authentication")

# 3. Get a token (you'll need to provide this)
token = input("\n2. Please paste your JWT token (from browser localStorage): ").strip()

if not token:
    print("❌ No token provided. Cannot continue.")
    exit(1)

# 4. Test with auth
headers = {"Authorization": f"Bearer {token}"}

print("\n3. Testing resume endpoint WITH auth:")
response = requests.get(f"{base_url}/resumes/", headers=headers)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Success! Found {len(data)} resumes")
    
    if len(data) > 0:
        print("\n   First 3 resumes:")
        for i, resume in enumerate(data[:3]):
            print(f"   {i+1}. {resume.get('first_name', 'N/A')} {resume.get('last_name', 'N/A')} - {resume.get('current_title', 'N/A')}")
    else:
        print("   ⚠️ No resumes found for this user")
        
        # Check user info
        print("\n4. Checking user info:")
        user_response = requests.get(f"{base_url}/users/me", headers=headers)
        if user_response.status_code == 200:
            user = user_response.json()
            print(f"   User: {user.get('email')}")
            print(f"   ID: {user.get('id')}")
            print(f"   Name: {user.get('full_name', 'N/A')}")
        else:
            print(f"   ❌ Could not get user info: {user_response.status_code}")
else:
    print(f"   ❌ Error: {response.status_code}")
    print(f"   Response: {response.text[:200]}...")
    
    if response.status_code == 401:
        print("\n   Token might be invalid or expired.")
        print("   Try generating a new token.")

# 5. Test search endpoint
print("\n5. Testing search endpoint:")
search_data = {
    "query": "python developer",
    "limit": 5
}
response = requests.post(f"{base_url}/search/", headers=headers, json=search_data)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    results = response.json()
    print(f"   ✅ Search returned {len(results)} results")
else:
    print(f"   ❌ Search error: {response.status_code}")