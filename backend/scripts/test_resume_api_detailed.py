#!/usr/bin/env python3
"""Test resume API with different parameters."""

import requests
import json

print("="*60)
print("RESUME API DETAILED TEST")
print("="*60)

token = input("\nPaste your access token: ").strip()

if not token:
    print("❌ No token provided")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}
base_url = "http://localhost:8001/api/v1"

# Test 1: Default parameters
print("\n1. Testing with default parameters (no skip/limit):")
try:
    response = requests.get(f"{base_url}/resumes/", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Returned {len(data)} resumes")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: With limit=100
print("\n2. Testing with limit=100:")
try:
    response = requests.get(f"{base_url}/resumes/?skip=0&limit=100", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Returned {len(data)} resumes")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: With limit=1000
print("\n3. Testing with limit=1000:")
try:
    response = requests.get(f"{base_url}/resumes/?skip=0&limit=1000", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Returned {len(data)} resumes")
        if len(data) > 0:
            print(f"   First resume: {data[0]['first_name']} {data[0]['last_name']}")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Test pagination
print("\n4. Testing pagination:")
try:
    # First page
    response1 = requests.get(f"{base_url}/resumes/?skip=0&limit=50", headers=headers)
    if response1.status_code == 200:
        page1 = response1.json()
        print(f"   Page 1 (skip=0, limit=50): {len(page1)} resumes")
    
    # Second page
    response2 = requests.get(f"{base_url}/resumes/?skip=50&limit=50", headers=headers)
    if response2.status_code == 200:
        page2 = response2.json()
        print(f"   Page 2 (skip=50, limit=50): {len(page2)} resumes")
    
    # Third page
    response3 = requests.get(f"{base_url}/resumes/?skip=100&limit=50", headers=headers)
    if response3.status_code == 200:
        page3 = response3.json()
        print(f"   Page 3 (skip=100, limit=50): {len(page3)} resumes")
    
    # Fourth page
    response4 = requests.get(f"{base_url}/resumes/?skip=150&limit=50", headers=headers)
    if response4.status_code == 200:
        page4 = response4.json()
        print(f"   Page 4 (skip=150, limit=50): {len(page4)} resumes")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Check user info
print("\n5. Checking current user:")
try:
    response = requests.get(f"{base_url}/users/me", headers=headers)
    if response.status_code == 200:
        user = response.json()
        print(f"   ✅ User: {user['email']} (ID: {user['id']})")
    else:
        print(f"   ❌ Error: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("BROWSER CONSOLE TEST")
print("="*60)
print("\nIf API works but browser doesn't, try this in browser console:")
print("""
// Get token and test API directly
const token = localStorage.getItem('access_token');
console.log('Token:', token);

// Test API
fetch('http://localhost:8001/api/v1/resumes/?skip=0&limit=1000', {
    headers: { 'Authorization': `Bearer ${token}` }
})
.then(r => r.json())
.then(data => console.log('Resumes:', data.length, data))
.catch(e => console.error('Error:', e));
""")