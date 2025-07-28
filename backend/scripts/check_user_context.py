#!/usr/bin/env python3
"""Check if API is returning resumes for the correct user."""

import requests
import jwt
import json

token = input("\nPaste your access token: ").strip()

if not token:
    print("❌ No token provided")
    exit(1)

# Decode token to see user info
try:
    # Decode without verification
    payload = jwt.decode(token, options={"verify_signature": False})
    print(f"\nToken info:")
    print(f"  sub (user_id): {payload.get('sub')}")
    print(f"  email: {payload.get('email', 'Not in token')}")
except Exception as e:
    print(f"Error decoding token: {e}")

headers = {"Authorization": f"Bearer {token}"}

# Get current user
print("\n1. Current user from API:")
response = requests.get("http://localhost:8001/api/v1/users/me", headers=headers)
if response.status_code == 200:
    user = response.json()
    print(f"   Email: {user['email']}")
    print(f"   ID: {user['id']}")
else:
    print(f"   Error: {response.status_code}")

# Test resume API with explicit pagination
print("\n2. Testing resume pagination:")
for page in range(3):
    skip = page * 100
    url = f"http://localhost:8001/api/v1/resumes/?skip={skip}&limit=100"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Page {page + 1} (skip={skip}): {len(data)} resumes")
        if len(data) > 0:
            print(f"     First: {data[0]['first_name']} {data[0]['last_name']}")
            print(f"     Last: {data[-1]['first_name']} {data[-1]['last_name']}")
    else:
        print(f"   Page {page + 1}: Error {response.status_code}")

# Test with large limit
print("\n3. Testing with large limit:")
response = requests.get("http://localhost:8001/api/v1/resumes/?skip=0&limit=500", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"   Returned {len(data)} resumes with limit=500")
else:
    print(f"   Error: {response.status_code}")