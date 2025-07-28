#!/usr/bin/env python3
"""Debug why user can't see resumes."""

import requests
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("="*60)
print("RESUME VISIBILITY DEBUG")
print("="*60)

# Step 1: Get token
print("\n1. Please get your token from the browser:")
print("   - Open http://localhost:3000")
print("   - Press F12 → Application → Local Storage → localhost:3000")
print("   - Copy the 'access_token' value")

token = input("\nPaste token here: ").strip()

if not token:
    print("❌ No token provided")
    exit(1)

# Step 2: Check user
print("\n2. Checking user...")
try:
    response = requests.get(
        "http://localhost:8001/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        user = response.json()
        user_id = user['id']
        email = user['email']
        print(f"   ✅ User: {email}")
        print(f"   ID: {user_id}")
    else:
        print(f"   ❌ Invalid token: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Step 3: Check resumes via API
print("\n3. Checking resumes via API...")
try:
    response = requests.get(
        "http://localhost:8001/api/v1/resumes/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        resumes = response.json()
        print(f"   API returned {len(resumes)} resumes")
        
        if len(resumes) > 0:
            print("\n   First 3 resumes:")
            for i, r in enumerate(resumes[:3]):
                print(f"   {i+1}. {r['first_name']} {r['last_name']} - {r.get('current_title', 'N/A')}")
    else:
        print(f"   ❌ API Error: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 4: Check database directly
print("\n4. Checking database directly...")
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    DATABASE_URL = "postgresql://promtitude:promtitude123@localhost:5433/promtitude"
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        # Count resumes for this user
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM resumes 
            WHERE user_id = :user_id
        """), {"user_id": user_id})
        
        count = result.scalar()
        print(f"   Database shows {count} resumes for user {user_id}")
        
        if count == 0:
            # Check if there are any resumes at all
            result = session.execute(text("SELECT COUNT(*) FROM resumes"))
            total = result.scalar()
            print(f"   Total resumes in database: {total}")
            
            if total > 0:
                # Show which users have resumes
                result = session.execute(text("""
                    SELECT u.email, COUNT(r.id) as count
                    FROM users u
                    JOIN resumes r ON u.id = r.user_id
                    GROUP BY u.id, u.email
                    ORDER BY count DESC
                    LIMIT 5
                """))
                
                print("\n   Users with resumes:")
                for row in result:
                    print(f"   - {row[0]}: {row[1]} resumes")
                    
                print(f"\n   ⚠️ User {email} has no resumes!")
                print("   Need to import resumes for this user.")
        else:
            # Get sample resumes
            result = session.execute(text("""
                SELECT first_name, last_name, current_title, created_at
                FROM resumes
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 5
            """), {"user_id": user_id})
            
            print("\n   Sample resumes from database:")
            for row in result:
                print(f"   - {row[0]} {row[1]} | {row[2]} | Created: {row[3]}")
                
except Exception as e:
    print(f"   ❌ Database error: {e}")

# Step 5: Import resumes if needed
print("\n" + "="*60)
print("SOLUTION")
print("="*60)

print("\nTo import test resumes for your user:")
print("1. Make sure you're logged in as the user who needs resumes")
print("2. Run: python import_resumes_simple.py")
print("\nOr to manually check the database:")
print("   psql -U promtitude -d promtitude -h localhost -p 5433")
print("   SELECT * FROM resumes WHERE user_id = 'YOUR_USER_ID';")

# Save user info
with open("current_user.txt", "w") as f:
    f.write(f"Email: {email}\n")
    f.write(f"User ID: {user_id}\n")
    f.write(f"Token (first 20 chars): {token[:20]}...\n")
    
print(f"\n✅ User info saved to current_user.txt")