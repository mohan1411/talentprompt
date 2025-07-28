#!/usr/bin/env python3
"""Test the API directly to see the exact error."""

import requests
import json

print("="*60)
print("TESTING API TO FIND EXACT ERROR")
print("="*60)

token = input("\nPaste your access token: ").strip()

if not token:
    print("❌ No token provided")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# First, verify we can fetch the first page
print("\n1. Testing first page (should work):")
response = requests.get("http://localhost:8001/api/v1/resumes/?skip=0&limit=10", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Returned {len(data)} resumes")

# Now test around the error boundary
print("\n2. Finding exact error boundary:")
for skip in [90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100]:
    response = requests.get(f"http://localhost:8001/api/v1/resumes/?skip={skip}&limit=1", headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"   skip={skip}: ✅ OK - {data[0]['first_name']} {data[0]['last_name']}")
        else:
            print(f"   skip={skip}: ⚠️ Empty result")
    else:
        print(f"   skip={skip}: ❌ Error {response.status_code}")
        # Try to get error details
        try:
            error_data = response.json()
            print(f"      Detail: {error_data.get('detail', 'No detail')}")
        except:
            print(f"      Response: {response.text[:200]}")

# Test if it's a limit issue
print("\n3. Testing different limits at skip=95:")
for limit in [1, 2, 5, 10]:
    response = requests.get(f"http://localhost:8001/api/v1/resumes/?skip=95&limit={limit}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   limit={limit}: ✅ OK - returned {len(data)} resumes")
    else:
        print(f"   limit={limit}: ❌ Error {response.status_code}")

# Test fetching specific resumes by getting their IDs first
print("\n4. Checking if specific resume IDs work:")
# Get all resume IDs from first 100
all_ids = []
for skip in range(0, 100, 10):
    response = requests.get(f"http://localhost:8001/api/v1/resumes/?skip={skip}&limit=10", headers=headers)
    if response.status_code == 200:
        data = response.json()
        all_ids.extend([r['id'] for r in data])

if len(all_ids) >= 100:
    # Try to fetch resume at position 95 directly
    resume_id_95 = all_ids[95] if len(all_ids) > 95 else None
    if resume_id_95:
        print(f"\n   Testing direct fetch of resume at position 95 (ID: {resume_id_95}):")
        response = requests.get(f"http://localhost:8001/api/v1/resumes/{resume_id_95}", headers=headers)
        if response.status_code == 200:
            print("   ✅ Direct fetch works!")
        else:
            print(f"   ❌ Direct fetch fails with {response.status_code}")

print("\n" + "="*60)
print("CHECK YOUR BACKEND LOGS!")
print("="*60)
print("\nThe backend terminal should show the actual Python error.")
print("Look for a traceback that shows what's failing.")
print("\nCommon issues:")
print("- JSON serialization error (invalid data type)")
print("- Database query timeout")
print("- Memory issue with large fields")
print("- Null value in a required field")