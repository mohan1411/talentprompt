#!/usr/bin/env python3
"""Generate OAuth token and create callback URL."""

import asyncio
import asyncpg
import os
from datetime import datetime, timedelta, timezone
import jwt
from uuid import uuid4
import webbrowser
import urllib.parse

# Load environment variables
from load_env import load_env
load_env()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:promtitude123@localhost:5433/promtitude")
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-min-32-chars-long-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "11520"))


async def get_user_and_generate_token(email: str):
    """Get user and generate token."""
    # Convert SQLAlchemy URL to asyncpg format
    db_url = DATABASE_URL
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgres://")
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgres://")
    
    try:
        conn = await asyncpg.connect(db_url)
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None
    
    try:
        user = await conn.fetchrow("""
            SELECT id, email, full_name, is_active
            FROM users 
            WHERE email = $1
        """, email)
        
        if not user:
            print(f"❌ User {email} not found")
            return None
        
        if not user['is_active']:
            print(f"⚠️  User {email} is not active")
        
        # Generate token
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": str(user["id"]),  # Use user ID, not email, to match production behavior
            "user_id": str(user["id"]),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid4())
        }
        
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "token": token,
            "user": dict(user)
        }
        
    finally:
        await conn.close()


async def main():
    """Generate token and create OAuth callback URL."""
    print("="*60)
    print("OAUTH TOKEN HELPER")
    print("="*60)
    
    email = input("\nEnter email (or press Enter for promtitude@gmail.com): ").strip()
    if not email:
        email = "promtitude@gmail.com"
    
    print(f"\nGenerating token for: {email}")
    
    result = await get_user_and_generate_token(email)
    
    if not result:
        return
    
    token = result["token"]
    user = result["user"]
    
    print(f"\n✅ Token generated successfully!")
    print(f"   User ID: {user['id']}")
    print(f"   Name: {user['full_name']}")
    
    # Create OAuth callback URL
    callback_base = "http://localhost:3000/auth/google/callback"
    params = {
        "token": token,
        "state": "dummy_state"  # Your app might check this
    }
    
    callback_url = f"{callback_base}?{urllib.parse.urlencode(params)}"
    
    print("\n" + "="*60)
    print("OPTION 1: Automatic (Opens in browser)")
    print("="*60)
    print("Press Enter to open the OAuth callback URL in your browser...")
    print("This will simulate a successful OAuth login.")
    input()
    
    webbrowser.open(callback_url)
    print("✓ Opened in browser!")
    
    print("\n" + "="*60)
    print("OPTION 2: Manual")
    print("="*60)
    print("Copy and paste this URL in your browser:")
    print(callback_url)
    
    print("\n" + "="*60)
    print("OPTION 3: Direct Token (Advanced)")
    print("="*60)
    print("Run this in browser console:")
    print(f"""
// Set token and reload
localStorage.setItem('access_token', '{token[:50]}...');
window.location.href = '/dashboard';
""")
    
    print("\n✅ The OAuth callback will handle everything properly!")


if __name__ == "__main__":
    asyncio.run(main())