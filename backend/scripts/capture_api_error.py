#!/usr/bin/env python3
"""Capture the exact API error at position 95."""

import requests
import json

print("="*60)
print("CAPTURING API ERROR AT POSITION 95")
print("="*60)

token = input("\nPaste your access token: ").strip()

if not token:
    print("❌ No token provided")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# First verify we can access resumes
print("\n1. Testing basic access...")
response = requests.get("http://localhost:8001/api/v1/resumes/?skip=0&limit=1", headers=headers)
if response.status_code != 200:
    print(f"❌ Cannot access resumes: {response.status_code}")
    exit(1)

print("✅ Basic access works")

# Find exact error position
print("\n2. Finding exact error position...")
error_position = None
last_working = None

for skip in range(90, 110):
    response = requests.get(f"http://localhost:8001/api/v1/resumes/?skip={skip}&limit=1", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"   skip={skip}: ✅ OK - {data[0]['first_name']} {data[0]['last_name']}")
            last_working = skip
        else:
            print(f"   skip={skip}: ⚠️ Empty result")
    else:
        print(f"   skip={skip}: ❌ ERROR {response.status_code}")
        if error_position is None:
            error_position = skip
            print(f"\n   ERROR STARTS AT POSITION {skip}!")
            
            # Try to get error details
            try:
                error_data = response.json()
                print(f"   Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Raw response: {response.text[:500]}")
            
            print("\n   ⚠️ CHECK YOUR BACKEND TERMINAL NOW!")
            print("   The Python traceback should be visible there.")
            break

if error_position:
    print(f"\n3. Summary:")
    print(f"   - Last working position: {last_working}")
    print(f"   - First error position: {error_position}")
    print(f"   - Total working resumes: {error_position}")
    
    print("\n4. Testing if individual resume fetch works...")
    # Get all IDs up to error position
    all_resumes = []
    for skip in range(0, error_position, 10):
        response = requests.get(f"http://localhost:8001/api/v1/resumes/?skip={skip}&limit=10", headers=headers)
        if response.status_code == 200:
            all_resumes.extend(response.json())
    
    if len(all_resumes) >= error_position:
        # Try to fetch the last working resume directly
        last_working_id = all_resumes[last_working]['id'] if last_working < len(all_resumes) else None
        if last_working_id:
            response = requests.get(f"http://localhost:8001/api/v1/resumes/{last_working_id}", headers=headers)
            if response.status_code == 200:
                print(f"   ✅ Direct fetch of last working resume works")
            else:
                print(f"   ❌ Direct fetch fails: {response.status_code}")
else:
    print("\n✅ No errors found! All positions work.")

print("\n" + "="*60)
print("NEXT STEPS")
print("="*60)
print("\n1. Check your backend terminal for the Python error traceback")
print("2. The error message will tell us exactly what's wrong")
print("3. Common issues:")
print("   - TypeError: Object of type X is not JSON serializable")
print("   - ValidationError: field required")
print("   - ValueError: invalid array")
print("\n4. Once you have the error, we can implement a proper fix")