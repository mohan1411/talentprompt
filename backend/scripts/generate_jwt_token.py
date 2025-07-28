#!/usr/bin/env python3
"""Generate JWT token for OAuth user without API call."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
from jose import jwt
from uuid import uuid4
import asyncio
import asyncpg

# Load environment
from load_env import load_env
load_env()

# Get settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:promtitude123@localhost:5433/promtitude")
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-min-32-chars-long-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 11520  # 8 days

async def get_user_id(email: str):
    """Get user ID from database."""
    # Convert to asyncpg format
    db_url = DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgres://")
    
    try:
        conn = await asyncpg.connect(db_url)
        user = await conn.fetchrow(
            "SELECT id, email, full_name FROM users WHERE email = $1",
            email
        )
        await conn.close()
        
        if user:
            return str(user['id']), user['full_name']
        return None, None
    except Exception as e:
        print(f"Database error: {e}")
        return None, None

def generate_token(email: str, user_id: str):
    """Generate JWT token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": user_id,  # Use user ID, not email, to match production behavior
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid4())
    }
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def main():
    print("="*60)
    print("JWT TOKEN GENERATOR")
    print("="*60)
    
    email = input("\nEnter email (or press Enter for promtitude@gmail.com): ").strip()
    if not email:
        email = "promtitude@gmail.com"
    
    print(f"\nLooking up user: {email}")
    
    user_id, full_name = await get_user_id(email)
    
    if not user_id:
        print(f"\n❌ User {email} not found in database")
        print("\nYou can create a token with a dummy user ID for testing:")
        user_id = input("Enter user ID (or press Enter to use a test UUID): ").strip()
        if not user_id:
            user_id = str(uuid4())
            print(f"Using test UUID: {user_id}")
    else:
        print(f"✓ Found user: {full_name} (ID: {user_id})")
    
    # Generate token
    token = generate_token(email, user_id)
    
    print("\n" + "="*60)
    print("TOKEN GENERATED")
    print("="*60)
    print(f"\nToken (copy this entire line):\n{token}")
    
    print("\n" + "="*60)
    print("HOW TO USE")
    print("="*60)
    print("\n1. Open your browser and go to: http://localhost:3000")
    print("\n2. Open browser console (F12 → Console)")
    print("\n3. Paste these commands:")
    print(f"""
// Set token and redirect
localStorage.setItem('access_token', '{token[:50]}...');
window.location.href = '/dashboard';
""")
    
    print("\n4. The full token has been printed above - copy it and replace the '...' part")
    
    # Also save to file for convenience
    with open('generated_token.txt', 'w') as f:
        f.write(f"Email: {email}\n")
        f.write(f"User ID: {user_id}\n")
        f.write(f"Token: {token}\n")
    
    print(f"\n✓ Token also saved to: generated_token.txt")

if __name__ == "__main__":
    asyncio.run(main())