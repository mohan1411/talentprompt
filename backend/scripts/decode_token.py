#!/usr/bin/env python3
"""Decode JWT token to see what's inside."""

import jwt
import json
from datetime import datetime
import base64

print("="*60)
print("JWT TOKEN DECODER")
print("="*60)

token = input("\nPaste your JWT token: ").strip()

if not token:
    print("❌ No token provided")
    exit(1)

# Decode without verification first
print("\n1. Decoding token header and payload...")
try:
    parts = token.split('.')
    if len(parts) != 3:
        print("❌ Invalid token format")
        exit(1)
    
    # Decode header
    header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
    print(f"\nHeader: {json.dumps(header, indent=2)}")
    
    # Decode payload
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
    print(f"\nPayload: {json.dumps(payload, indent=2)}")
    
    # Check expiration
    if 'exp' in payload:
        exp_date = datetime.fromtimestamp(payload['exp'])
        now = datetime.now()
        if exp_date < now:
            print(f"\n⚠️ Token is EXPIRED!")
            print(f"   Expired at: {exp_date}")
        else:
            print(f"\n✅ Token is valid until: {exp_date}")
    
    # Extract key info
    print("\n2. Key Information:")
    print(f"   User ID (sub): {payload.get('sub', 'N/A')}")
    print(f"   Email: {payload.get('email', 'N/A')}")
    print(f"   User ID: {payload.get('user_id', 'N/A')}")
    
except Exception as e:
    print(f"❌ Error decoding token: {e}")

# Try to verify with known secret
print("\n3. Trying to verify token with default secret...")
try:
    SECRET_KEY = "your-super-secret-key-min-32-chars-long-change-this"
    decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    print("✅ Token is valid with default secret key")
except jwt.ExpiredSignatureError:
    print("⚠️ Token is expired")
except jwt.InvalidTokenError as e:
    print(f"❌ Token verification failed: {e}")
    print("   This might mean a different secret key was used")

print("\n" + "="*60)
print("TOKEN ANALYSIS")
print("="*60)

if 'sub' in payload:
    print("\nToken Subject (sub) field contains:")
    sub_value = payload['sub']
    print(f"  Value: {sub_value}")
    
    # Check if it looks like a UUID or an email
    if '@' in str(sub_value):
        print("  ⚠️  WARNING: Token has email in 'sub' field!")
        print("  This is likely from a dev endpoint or script.")
        print("  Production tokens should have user ID in 'sub' field.")
    else:
        print("  ✅ Token has user ID in 'sub' field (correct format)")

print("\nIf you're having authentication issues:")
print("1. Clear browser storage and login fresh")
print("2. Make sure you're using the production OAuth flow")
print("3. Avoid using dev endpoints or scripts for token generation")

print("\nTo clear storage and login fresh:")
print("1. Open http://localhost:3000")
print("2. Open DevTools (F12)")
print("3. Application → Storage → Clear site data")
print("4. Refresh the page")
print("5. Login again with Google OAuth")