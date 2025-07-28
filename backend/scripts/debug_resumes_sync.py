#!/usr/bin/env python3
"""Debug resume visibility issues - synchronous version."""

import os
import sys
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("="*60)
    print("RESUME DEBUG TOOL (SYNC)")
    print("="*60)
    
    try:
        # Import models
        from app.models.user import User
        from app.models.resume import Resume
        
        # Get database URL and convert to sync format
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:promtitude123@localhost:5433/promtitude")
        
        # Remove async driver if present
        if "+asyncpg" in DATABASE_URL:
            DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")
        
        print(f"\n1. Connecting to database...")
        print(f"   URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
        
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        
        with Session() as session:
            # Find user
            email = "promtitude@gmail.com"
            user = session.query(User).filter(User.email == email).first()
            
            if not user:
                print(f"\n❌ User {email} not found!")
                
                # List all users
                users = session.query(User).limit(10).all()
                print("\nAvailable users:")
                for u in users:
                    print(f"  - {u.email} (ID: {u.id})")
                    
                return None
            else:
                print(f"\n✅ Found user: {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Name: {user.full_name}")
                print(f"   Active: {user.is_active}")
                
                # Count resumes for this user
                resumes = session.query(Resume).filter(Resume.user_id == user.id).all()
                
                print(f"\n2. Resume count for {email}: {len(resumes)}")
                
                if resumes:
                    print("\n   First 5 resumes:")
                    for i, resume in enumerate(resumes[:5]):
                        print(f"   {i+1}. {resume.first_name} {resume.last_name}")
                        print(f"      Title: {resume.current_title}")
                        print(f"      Status: {resume.status}")
                        print(f"      Created: {resume.created_at}")
                else:
                    print("\n   ⚠️ No resumes found for this user!")
                    
                    # Check total resumes in system
                    total_resumes = session.query(Resume).count()
                    print(f"\n3. Total resumes in database: {total_resumes}")
                    
                    if total_resumes > 0:
                        # Find which users have resumes using raw SQL
                        result = session.execute(text("""
                            SELECT u.email, COUNT(r.id) as resume_count
                            FROM users u
                            JOIN resumes r ON u.id = r.user_id
                            GROUP BY u.id, u.email
                            ORDER BY resume_count DESC
                            LIMIT 5
                        """))
                        
                        print("\n   Users with resumes:")
                        for row in result:
                            print(f"   - {row[0]}: {row[1]} resumes")
                
                # Save user ID to file for reference
                with open('user_id.txt', 'w') as f:
                    f.write(f"{user.id}\n")
                print(f"\n✅ User ID saved to user_id.txt: {user.id}")
                
                # Generate a working token
                print("\n4. Generating authentication token...")
                
                from datetime import datetime, timedelta
                import jwt
                from uuid import uuid4
                
                SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-min-32-chars-long-change-this")
                
                expire = datetime.utcnow() + timedelta(days=8)
                token_data = {
                    "sub": str(user.id),  # Use user ID, not email, to match production behavior
                    "user_id": str(user.id),
                    "exp": expire,
                    "iat": datetime.utcnow(),
                    "jti": str(uuid4())
                }
                
                token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
                
                # Save token to file
                with open('token.txt', 'w') as f:
                    f.write(token)
                print("✅ Token saved to token.txt")
                
                # Create login HTML
                html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Login as {user.email}</title>
    <style>
        body {{ font-family: Arial; padding: 50px; background: #f0f0f0; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; max-width: 800px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        button {{ background: #28a745; color: white; border: none; padding: 15px 30px; font-size: 18px; border-radius: 5px; cursor: pointer; width: 100%; margin: 10px 0; }}
        button:hover {{ background: #218838; }}
        .info {{ background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0; border: 1px solid #bee5eb; }}
        .warning {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border: 1px solid #ffeeba; }}
        code {{ background: #f8f9fa; padding: 2px 5px; border-radius: 3px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✅ Login Ready for {user.email}</h1>
        
        <div class="info">
            <strong>User ID:</strong> {user.id}<br>
            <strong>Email:</strong> {user.email}<br>
            <strong>Name:</strong> {user.full_name}<br>
            <strong>Resumes:</strong> {len(resumes)}
        </div>
        
        {'<div class="warning">⚠️ <strong>No resumes found!</strong><br>You may need to import resumes for this user.</div>' if len(resumes) == 0 else ''}
        
        <button onclick="login()">Login to Promtitude Dashboard</button>
        
        <p>If the button doesn't work, open console (F12) and run:</p>
        <code>localStorage.setItem('access_token', 'TOKEN_FROM_token.txt'); location.href='/dashboard';</code>
    </div>
    
    <script>
        const token = '{token}';
        
        function login() {{
            localStorage.setItem('access_token', token);
            alert('Token set! Redirecting to dashboard...');
            window.location.href = 'http://localhost:3000/dashboard';
        }}
    </script>
</body>
</html>"""
                
                with open('login_page.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                print("\n✅ Created login_page.html")
                
                return str(user.id)
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    user_id = main()
    
    if user_id:
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"\n✅ User ID: {user_id}")
        print("\nFiles created:")
        print("  - user_id.txt (contains user ID)")
        print("  - token.txt (contains JWT token)")
        print("  - login_page.html (click to login)")
        print("\nTo login:")
        print("  1. Open login_page.html in your browser")
        print("  2. Click the green login button")
        print("\nTo import test resumes (if needed):")
        print(f"  python import_test_resumes.py")