#!/usr/bin/env python3
"""Debug why resumes show in search but not in resume page."""

import requests
import json

print("="*60)
print("RESUME PAGE vs SEARCH DEBUG")
print("="*60)

token = input("\nPaste your access token: ").strip()

if not token:
    print("❌ No token provided")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}
base_url = "http://localhost:8001/api/v1"

# Test 1: Get current user
print("\n1. Checking current user...")
try:
    response = requests.get(f"{base_url}/users/me", headers=headers)
    if response.status_code == 200:
        user = response.json()
        print(f"   ✅ User: {user['email']} (ID: {user['id']})")
        user_id = user['id']
    else:
        print(f"   ❌ Error: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 2: Resume endpoint (what resume page uses)
print("\n2. Testing /resumes/ endpoint (resume page)...")
try:
    response = requests.get(f"{base_url}/resumes/", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        resumes = response.json()
        print(f"   ✅ Found {len(resumes)} resumes")
        if len(resumes) > 0:
            print(f"   First resume: {resumes[0]['first_name']} {resumes[0]['last_name']}")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Search endpoint
print("\n3. Testing /search/ endpoint...")
try:
    search_data = {
        "query": "python developer",
        "limit": 10
    }
    response = requests.post(f"{base_url}/search/", headers=headers, json=search_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        results = response.json()
        print(f"   ✅ Found {len(results)} search results")
        if len(results) > 0:
            print(f"   First result: {results[0]['first_name']} {results[0]['last_name']}")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Direct database check
print("\n4. Checking database directly...")
print("   Running SQL query to count resumes...")

from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://promtitude:promtitude123@localhost:5433/promtitude"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check resumes for current user
    result = conn.execute(text("""
        SELECT COUNT(*) as count, 
               MIN(created_at) as oldest,
               MAX(created_at) as newest
        FROM resumes 
        WHERE user_id = :user_id
        AND status != 'deleted'
    """), {"user_id": user_id})
    
    row = result.fetchone()
    print(f"   Resumes for user {user_id}: {row[0]}")
    if row[0] > 0:
        print(f"   Oldest: {row[1]}")
        print(f"   Newest: {row[2]}")
    
    # Check all resumes
    result = conn.execute(text("""
        SELECT u.email, COUNT(r.id) as resume_count
        FROM users u
        LEFT JOIN resumes r ON u.id = r.user_id AND r.status != 'deleted'
        GROUP BY u.id, u.email
        HAVING COUNT(r.id) > 0
        ORDER BY resume_count DESC
        LIMIT 5
    """))
    
    print("\n   Users with resumes:")
    for row in result:
        print(f"   - {row[0]}: {row[1]} resumes")

print("\n" + "="*60)
print("DIAGNOSIS")
print("="*60)

print("""
If search works but resume page doesn't:
1. The endpoints might be using different user contexts
2. There might be a filter issue in the resume endpoint
3. The frontend might be caching old data

Try these in your browser console:
""")

print("""
// Clear cache and test API directly
localStorage.removeItem('resumes_cache');
sessionStorage.clear();

// Test the API
fetch('http://localhost:8001/api/v1/resumes/', {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
})
.then(r => r.json())
.then(data => {
    console.log('Resume API returned:', data.length, 'resumes');
    console.log('First 3:', data.slice(0, 3));
});

// Force reload the page
window.location.reload(true);
""")