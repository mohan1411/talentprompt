#!/usr/bin/env python3
"""Debug the 500 error when fetching page 2."""

import requests
import json

token = input("\nPaste your access token: ").strip()

if not token:
    print("❌ No token provided")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

print("="*60)
print("DEBUGGING 500 ERROR")
print("="*60)

# Test different skip values to find where it breaks
print("\n1. Testing different skip values:")
test_skips = [0, 50, 75, 90, 95, 98, 99, 100, 101, 102, 105, 110, 150]

for skip in test_skips:
    url = f"http://localhost:8001/api/v1/resumes/?skip={skip}&limit=10"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   skip={skip}, limit=10: ✅ {len(data)} resumes")
        else:
            print(f"   skip={skip}, limit=10: ❌ Error {response.status_code}")
            if response.status_code == 500:
                try:
                    error_detail = response.json()
                    print(f"     Error detail: {error_detail}")
                except:
                    print(f"     Error text: {response.text[:200]}")
    except Exception as e:
        print(f"   skip={skip}: Exception: {e}")

# Test with smaller limit on page 2
print("\n2. Testing page 2 with smaller limits:")
for limit in [1, 5, 10, 20, 50, 100]:
    url = f"http://localhost:8001/api/v1/resumes/?skip=100&limit={limit}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   skip=100, limit={limit}: ✅ {len(data)} resumes")
        if len(data) > 0:
            print(f"     First: {data[0]['first_name']} {data[0]['last_name']}")
    else:
        print(f"   skip=100, limit={limit}: ❌ Error {response.status_code}")

# Check if it's a specific resume causing the issue
print("\n3. Binary search for problematic resume:")
skip = 95
limit = 10
while skip < 110:
    url = f"http://localhost:8001/api/v1/resumes/?skip={skip}&limit={limit}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   skip={skip}, limit={limit}: ✅ OK")
    else:
        print(f"   skip={skip}, limit={limit}: ❌ Error {response.status_code}")
        # Try smaller limit
        if limit > 1:
            limit = limit // 2
        else:
            skip += 1
            limit = 10
    
    if response.status_code == 200:
        skip += limit

print("\n" + "="*60)
print("CHECKING BACKEND LOGS")
print("="*60)
print("\nCheck your backend terminal for error messages.")
print("The 500 error should show a stack trace indicating what's wrong.")
print("\nCommon causes:")
print("1. Serialization error (invalid data in a resume)")
print("2. Database connection timeout")
print("3. Memory issue with large result sets")
print("4. Missing or null required fields")