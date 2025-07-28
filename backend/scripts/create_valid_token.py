#!/usr/bin/env python3
"""Create a valid token for promtitude@gmail.com."""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.security import create_access_token

print("="*60)
print("CREATING VALID TOKEN")
print("="*60)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:promtitude123@localhost:5433/promtitude")
if "+asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

with Session() as session:
    # Find user
    email = "promtitude@gmail.com"
    user = session.query(User).filter(User.email == email).first()
    
    if not user:
        print(f"❌ User {email} not found!")
        print("\nLet's check what users exist:")
        users = session.query(User).all()
        for u in users:
            print(f"  - {u.email} (ID: {u.id})")
        exit(1)
    
    print(f"✅ Found user: {user.email}")
    print(f"   ID: {user.id}")
    print(f"   Active: {user.is_active}")
    
    # Create token using the same function the app uses
    access_token_expires = timedelta(days=8)
    token = create_access_token(
        subject=str(user.id),  # This is the key - must be user ID, not email!
        expires_delta=access_token_expires
    )
    
    print(f"\n✅ Token created successfully!")
    print(f"\nToken:\n{token}")
    
    # Save to file
    with open("valid_token.txt", "w") as f:
        f.write(token)
    print(f"\nToken saved to: valid_token.txt")
    
    # Create HTML file for easy use
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Login as {user.email}</title>
    <style>
        body {{ font-family: Arial; padding: 50px; text-align: center; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #f5f5f5; padding: 40px; border-radius: 10px; }}
        button {{ background: #4CAF50; color: white; padding: 15px 30px; font-size: 18px; border: none; border-radius: 5px; cursor: pointer; }}
        button:hover {{ background: #45a049; }}
        .info {{ background: #e3f2fd; padding: 20px; margin: 20px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Login as {user.email}</h1>
        <div class="info">
            <p><strong>User ID:</strong> {user.id}</p>
            <p><strong>Token created:</strong> {datetime.now()}</p>
            <p><strong>Expires:</strong> {datetime.now() + access_token_expires}</p>
        </div>
        <button onclick="login()">Click to Login</button>
    </div>
    <script>
        const token = `{token}`;
        function login() {{
            // Clear old storage
            localStorage.clear();
            sessionStorage.clear();
            
            // Set new token
            localStorage.setItem('access_token', token);
            
            // Redirect to dashboard
            alert('Logged in! Redirecting to dashboard...');
            window.location.href = 'http://localhost:3000/dashboard';
        }}
    </script>
</body>
</html>"""
    
    with open("login_valid.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ Created login_valid.html")
    
    # Check resumes
    from app.models.resume import Resume
    resumes = session.query(Resume).filter(Resume.user_id == user.id).count()
    print(f"\n📄 This user has {resumes} resumes")
    
    if resumes == 0:
        print("\n⚠️ No resumes found! Run: python import_resumes_simple.py")