#!/usr/bin/env python3
"""Direct login helper - finds user and generates token."""

import psycopg2
import os
from datetime import datetime, timedelta
import jwt
from uuid import uuid4

# Load environment
try:
    from load_env import load_env
    load_env()
except:
    print("Warning: Could not load environment")

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:promtitude123@localhost:5433/promtitude")
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-min-32-chars-long-change-this")

print("="*60)
print("DIRECT LOGIN HELPER")
print("="*60)

# Step 1: Connect to database and find user
print("\n1. Connecting to database...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Find the user
    email = "promtitude@gmail.com"
    cur.execute("SELECT id, email, full_name, is_active FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    
    if not user:
        print(f"❌ User {email} not found!")
        # List all users
        cur.execute("SELECT email FROM users LIMIT 10")
        users = cur.fetchall()
        print("\nAvailable users:")
        for u in users:
            print(f"  - {u[0]}")
    else:
        user_id, email, full_name, is_active = user
        print(f"✅ Found user: {email}")
        print(f"   ID: {user_id}")
        print(f"   Name: {full_name}")
        print(f"   Active: {is_active}")
        
        # Step 2: Generate token
        print("\n2. Generating JWT token...")
        
        expire = datetime.utcnow() + timedelta(days=8)
        token_data = {
            "sub": str(user.id),  # Use user ID, not email, to match production behavior
            "user_id": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid4())
        }
        
        token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
        
        print("✅ Token generated!")
        
        # Step 3: Create HTML file for easy login
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Login as {email}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: #f0f0f0;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        button {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px;
        }}
        button:hover {{
            background: #45a049;
        }}
        .token-box {{
            background: #f0f0f0;
            padding: 10px;
            margin: 20px 0;
            border-radius: 4px;
            word-break: break-all;
            font-family: monospace;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Login as {email}</h1>
        <p>Click the button below to login:</p>
        
        <button onclick="login()">Login to Promtitude</button>
        
        <div class="token-box">
            Token (first 50 chars): {token[:50]}...
        </div>
        
        <p style="color: #666; margin-top: 20px;">
            If the button doesn't work, open browser console (F12) and run:<br>
            <code>localStorage.setItem('access_token', 'TOKEN_HERE'); location.href='/dashboard';</code>
        </p>
    </div>
    
    <script>
        const token = '{token}';
        
        function login() {{
            // Store token
            localStorage.setItem('access_token', token);
            
            // Redirect to dashboard
            window.location.href = 'http://localhost:3000/dashboard';
        }}
        
        // Also log to console for debugging
        console.log('Token ready. Click the button or run: login()');
    </script>
</body>
</html>"""
        
        # Save HTML file
        html_file = "login_helper.html"
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print(f"\n✅ Created {html_file}")
        print(f"\n3. To login:")
        print(f"   a) Open this file in your browser: {os.path.abspath(html_file)}")
        print(f"   b) Click the 'Login to Promtitude' button")
        
        # Also save token to text file
        with open("token.txt", 'w') as f:
            f.write(token)
        print(f"\n   Token also saved to: token.txt")
        
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Database error: {e}")
    print("\nMake sure:")
    print("1. PostgreSQL is running")
    print("2. Database URL is correct")
    print("3. The database 'promtitude' exists")