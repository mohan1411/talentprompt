#!/usr/bin/env python3
"""Create a valid token without importing app settings."""

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import jwt
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.user import User

print("="*60)
print("CREATING VALID TOKEN (SIMPLE)")
print("="*60)

# Configuration
DATABASE_URL = "postgresql://promtitude:promtitude123@localhost:5433/promtitude"
SECRET_KEY = "your-super-secret-key-min-32-chars-long-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 8  # 8 days

# Database connection
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def create_access_token(subject: str, expires_delta: timedelta = None) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire, 
        "sub": str(subject)  # This MUST be the user ID, not email!
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

with Session() as session:
    # Find user
    email = "promtitude@gmail.com"
    user = session.query(User).filter(User.email == email).first()
    
    if not user:
        print(f"❌ User {email} not found!")
        print("\nChecking what users exist...")
        users = session.query(User).limit(10).all()
        for u in users:
            print(f"  - {u.email} (ID: {u.id})")
        exit(1)
    
    print(f"✅ Found user: {user.email}")
    print(f"   ID: {user.id}")
    print(f"   Active: {user.is_active}")
    
    # Create token
    access_token_expires = timedelta(days=8)
    token = create_access_token(
        subject=str(user.id),  # Using user ID, not email!
        expires_delta=access_token_expires
    )
    
    print(f"\n✅ Token created successfully!")
    
    # Decode to verify
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"\nToken payload:")
        print(f"   sub (user_id): {payload['sub']}")
        print(f"   exp: {datetime.fromtimestamp(payload['exp'])}")
    except Exception as e:
        print(f"Error decoding: {e}")
    
    # Save token
    with open("token_valid.txt", "w") as f:
        f.write(token)
    print(f"\nToken saved to: token_valid.txt")
    
    # Create HTML file
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Login as {user.email}</title>
    <style>
        body {{ 
            font-family: Arial; 
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
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
            text-align: center;
            max-width: 500px;
        }}
        button {{ 
            background: #4CAF50; 
            color: white; 
            padding: 15px 30px; 
            font-size: 18px; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            margin: 10px;
        }}
        button:hover {{ background: #45a049; }}
        .info {{ 
            background: #e3f2fd; 
            padding: 15px; 
            margin: 20px 0; 
            border-radius: 5px; 
            text-align: left;
        }}
        .warning {{
            background: #fff3cd;
            color: #856404;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Login as {user.email}</h1>
        
        <div class="info">
            <strong>User Details:</strong><br>
            Email: {user.email}<br>
            ID: {user.id}<br>
            Token expires: in 8 days
        </div>
        
        <button onclick="clearAndLogin()">Clear Storage & Login</button>
        <button onclick="justLogin()">Just Set Token</button>
        
        <div class="warning">
            If you still see "No resumes found" after logging in, 
            run: python import_resumes_simple.py
        </div>
    </div>
    
    <script>
        const token = `{token}`;
        
        function clearAndLogin() {{
            // Clear everything
            localStorage.clear();
            sessionStorage.clear();
            
            // Clear cookies
            document.cookie.split(";").forEach(function(c) {{ 
                document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
            }});
            
            // Set token
            localStorage.setItem('access_token', token);
            
            alert('Storage cleared and logged in! Redirecting...');
            window.location.href = 'http://localhost:3000/dashboard';
        }}
        
        function justLogin() {{
            localStorage.setItem('access_token', token);
            alert('Token set! Redirecting...');
            window.location.href = 'http://localhost:3000/dashboard';
        }}
    </script>
</body>
</html>"""
    
    with open("login_now.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ Created login_now.html")
    
    # Check resumes
    from app.models.resume import Resume
    resume_count = session.query(Resume).filter(Resume.user_id == user.id).count()
    print(f"\n📄 Resume count for {user.email}: {resume_count}")
    
    if resume_count == 0:
        print("\n⚠️ This user has NO resumes!")
        print("After logging in, run: python import_resumes_simple.py")
    else:
        print(f"\n✅ This user has {resume_count} resumes")
        
print("\n" + "="*60)
print("NEXT STEPS")
print("="*60)
print("\n1. Open login_now.html in your browser")
print("2. Click 'Clear Storage & Login'")
print("3. You should see your dashboard")
print("\nIf you still see 'No resumes found':")
print("- Make sure promtitude@gmail.com has resumes in the database")
print("- Run: python import_resumes_simple.py")