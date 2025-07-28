#!/usr/bin/env python3
"""Generate access token for OAuth users."""

import asyncio
import asyncpg
import os
from datetime import datetime, timedelta, timezone
import jwt
from uuid import uuid4

# Load environment variables
from load_env import load_env
load_env()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:promtitude123@localhost:5433/promtitude")
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-min-32-chars-long-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "11520"))  # 8 days


async def get_oauth_user(email: str):
    """Get OAuth user from database."""
    # Convert SQLAlchemy URL to asyncpg format
    db_url = DATABASE_URL
    print(f"Original DATABASE_URL format: {db_url.split('://')[0] if '://' in db_url else 'unknown'}")
    
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgres://")
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgres://")
    
    print(f"Converted to asyncpg format: {db_url.split('@')[0] if '@' in db_url else db_url[:30]}...")
    
    try:
        conn = await asyncpg.connect(db_url)
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print(f"   Attempted URL: {db_url}")
        return None
    
    try:
        user = await conn.fetchrow("""
            SELECT id, email, full_name, is_active
            FROM users 
            WHERE email = $1
        """, email)
        
        if user:
            print(f"✓ Found user: {email}")
            print(f"  ID: {user['id']}")
            print(f"  Name: {user['full_name']}")
            print(f"  Active: {user['is_active']}")
            # Check if oauth_provider column exists
            oauth_check = await conn.fetchrow("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'oauth_provider'
            """)
            
            if oauth_check:
                oauth_info = await conn.fetchrow("""
                    SELECT oauth_provider FROM users WHERE email = $1
                """, email)
                print(f"  OAuth Provider: {oauth_info.get('oauth_provider', 'None')}")
            return dict(user)
        else:
            print(f"❌ User not found: {email}")
            return None
            
    finally:
        await conn.close()


def create_access_token(user_data: dict) -> str:
    """Create JWT access token for user."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user_data["id"]),  # Use user ID, not email, to match production behavior
        "user_id": str(user_data["id"]),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid4())  # JWT ID for uniqueness
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def main():
    """Generate token for OAuth user."""
    print("="*60)
    print("OAUTH USER TOKEN GENERATOR")
    print("="*60)
    
    print(f"\nConfiguration:")
    print(f"  DATABASE_URL: {DATABASE_URL[:30]}...")
    print(f"  SECRET_KEY: {'Loaded' if SECRET_KEY != 'your-super-secret-key-min-32-chars-long-change-this' else 'Using default (WARNING!)'}")
    print(f"  Token expiry: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    
    email = input("Enter OAuth user email (or press Enter for promtitude@gmail.com): ").strip()
    if not email:
        email = "promtitude@gmail.com"
    
    print(f"\nGenerating token for: {email}")
    
    # Get user from database
    user = await get_oauth_user(email)
    
    if not user:
        print("\n❌ Cannot generate token - user not found")
        return
    
    if not user.get("is_active"):
        print("\n⚠️  Warning: User is not active")
    
    # Generate token
    token = create_access_token(user)
    
    print("\n✅ Access token generated successfully!")
    print("\n" + "="*60)
    print("ACCESS TOKEN:")
    print("="*60)
    print(token)
    print("="*60)
    
    print("\n📋 How to use this token:")
    print("\n1. In API requests (curl):")
    print(f'   curl -H "Authorization: Bearer {token[:50]}..." http://localhost:8001/api/v1/resumes/')
    
    print("\n2. In the frontend (browser console):")
    print("   localStorage.setItem('access_token', '<paste_token_here>');")
    print("   window.location.reload();")
    
    print("\n3. In Postman/Insomnia:")
    print("   Authorization: Bearer <token>")
    
    print(f"\n⏰ Token expires in: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes ({ACCESS_TOKEN_EXPIRE_MINUTES/60/24:.1f} days)")
    
    # Test the token
    print("\n🧪 Testing token...")
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("✓ Token is valid")
        print(f"  User ID: {decoded.get('user_id')}")
        print(f"  Email: {decoded.get('sub')}")
        print(f"  Expires: {datetime.fromtimestamp(decoded.get('exp'))}")
    except Exception as e:
        print(f"❌ Token validation failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())