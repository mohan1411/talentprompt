#!/usr/bin/env python3
"""Complete setup check for viewing resumes."""

import requests
import json
import subprocess
import time

print("="*60)
print("COMPLETE SETUP CHECK")
print("="*60)

# Step 1: Check backend
print("\n1. Checking Backend...")
try:
    response = requests.get("http://localhost:8001/api/v1/health/")
    if response.status_code == 200:
        print("   ✅ Backend is running on port 8001")
    else:
        print("   ❌ Backend returned status:", response.status_code)
except:
    print("   ❌ Backend is NOT running!")
    print("   Start it with:")
    print("     cd backend")
    print("     uvicorn app.main:app --reload --host 0.0.0.0 --port 8001")
    exit(1)

# Step 2: Check frontend
print("\n2. Checking Frontend...")
try:
    response = requests.get("http://localhost:3000/", timeout=5)
    print("   ✅ Frontend is running on port 3000")
except:
    print("   ❌ Frontend is NOT running!")
    print("   Start it with:")
    print("     cd frontend")
    print("     npm run dev")
    exit(1)

# Step 3: Get token from user
print("\n3. Authentication Check")
print("   To get your token:")
print("   a) Open http://localhost:3000 in Chrome")
print("   b) Press F12 to open DevTools")
print("   c) Go to Application tab → Local Storage → localhost:3000")
print("   d) Look for 'access_token' and copy its value")

token = input("\nPaste your token here (or press Enter to skip): ").strip()

if token:
    # Test token
    try:
        response = requests.get(
            "http://localhost:8001/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            user = response.json()
            print(f"\n   ✅ Token is valid!")
            print(f"   User: {user['email']}")
            print(f"   ID: {user['id']}")
            
            # Check resumes
            response = requests.get(
                "http://localhost:8001/api/v1/resumes/",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                resumes = response.json()
                print(f"\n   📄 Resume count: {len(resumes)}")
                if len(resumes) > 0:
                    print("   First 3 resumes:")
                    for i, r in enumerate(resumes[:3]):
                        print(f"   {i+1}. {r['first_name']} {r['last_name']} - {r.get('current_title', 'N/A')}")
                else:
                    print("   ⚠️ No resumes found for this user")
                    print("\n   To import test resumes:")
                    print("     cd backend/scripts")
                    print("     python import_resumes_simple.py")
            else:
                print(f"   ❌ Resume API error: {response.status_code}")
        else:
            print(f"   ❌ Invalid token: {response.status_code}")
            print("   You need to login again")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("QUICK FIX STEPS")
print("="*60)
print("\n1. Make sure both services are running:")
print("   Terminal 1: cd backend && uvicorn app.main:app --reload --port 8001")
print("   Terminal 2: cd frontend && npm run dev")
print("\n2. Open http://localhost:3000 in your browser")
print("\n3. If you see 'Failed to fetch resumes':")
print("   a) Open browser console (F12)")
print("   b) Look for CORS errors")
print("   c) Try clearing browser cache and cookies")
print("\n4. If resumes are empty, import test data:")
print("   cd backend/scripts")
print("   python import_resumes_simple.py")

# Create a complete test page
html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Resume Viewer Test</title>
    <style>
        body { font-family: Arial; padding: 20px; max-width: 1000px; margin: 0 auto; }
        .section { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 8px; }
        button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        button:hover { background: #45a049; }
        .error { color: red; background: #ffe0e0; padding: 10px; margin: 10px 0; border-radius: 4px; }
        .success { color: green; background: #e0ffe0; padding: 10px; margin: 10px 0; border-radius: 4px; }
        .resume { background: white; padding: 15px; margin: 10px 0; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        input { width: 100%; padding: 8px; margin: 5px 0; }
    </style>
</head>
<body>
    <h1>Resume Viewer Test</h1>
    
    <div class="section">
        <h2>Step 1: Enter Token</h2>
        <input type="text" id="token" placeholder="Paste your access token here">
        <button onclick="testToken()">Test Token</button>
        <div id="tokenResult"></div>
    </div>
    
    <div class="section">
        <h2>Step 2: Fetch Resumes</h2>
        <button onclick="fetchResumes()">Fetch Resumes</button>
        <div id="resumeCount"></div>
        <div id="resumeList"></div>
    </div>
    
    <div class="section">
        <h2>Step 3: Go to App</h2>
        <button onclick="goToApp()">Open Dashboard</button>
    </div>

    <script>
        async function testToken() {
            const token = document.getElementById('token').value;
            const result = document.getElementById('tokenResult');
            
            if (!token) {
                result.innerHTML = '<div class="error">Please enter a token</div>';
                return;
            }
            
            localStorage.setItem('access_token', token);
            
            try {
                const response = await fetch('http://localhost:8001/api/v1/users/me', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                if (response.ok) {
                    const user = await response.json();
                    result.innerHTML = `<div class="success">✅ Valid token for: ${user.email}</div>`;
                } else {
                    result.innerHTML = '<div class="error">❌ Invalid token</div>';
                }
            } catch (e) {
                result.innerHTML = `<div class="error">❌ Error: ${e.message}</div>`;
            }
        }
        
        async function fetchResumes() {
            const token = localStorage.getItem('access_token');
            const countDiv = document.getElementById('resumeCount');
            const listDiv = document.getElementById('resumeList');
            
            if (!token) {
                countDiv.innerHTML = '<div class="error">No token. Please test token first.</div>';
                return;
            }
            
            try {
                const response = await fetch('http://localhost:8001/api/v1/resumes/', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                if (response.ok) {
                    const resumes = await response.json();
                    countDiv.innerHTML = `<div class="success">Found ${resumes.length} resumes</div>`;
                    
                    listDiv.innerHTML = resumes.slice(0, 10).map(r => `
                        <div class="resume">
                            <strong>${r.first_name} ${r.last_name}</strong><br>
                            ${r.current_title || 'No title'}<br>
                            ${r.location || 'No location'}
                        </div>
                    `).join('');
                } else {
                    countDiv.innerHTML = `<div class="error">Error: ${response.status}</div>`;
                }
            } catch (e) {
                countDiv.innerHTML = `<div class="error">Fetch error: ${e.message}</div>`;
            }
        }
        
        function goToApp() {
            window.location.href = 'http://localhost:3000/dashboard';
        }
        
        // Auto-load token if exists
        window.onload = () => {
            const token = localStorage.getItem('access_token');
            if (token) {
                document.getElementById('token').value = token;
            }
        };
    </script>
</body>
</html>"""

with open("resume_test.html", "w") as f:
    f.write(html_content)

print("\n5. Created resume_test.html")
print("   Open it directly at: http://localhost:3000/resume_test.html")
print("   Or copy it to frontend/public/ directory")