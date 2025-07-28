#!/usr/bin/env python3
"""Quick token generator - minimal dependencies."""

import json
import base64
import hmac
import hashlib
from datetime import datetime, timedelta
import uuid

# Configuration
SECRET_KEY = "your-super-secret-key-min-32-chars-long-change-this"
email = "promtitude@gmail.com"
user_id = "00000000-0000-0000-0000-000000000001"  # We'll use a dummy ID for now

print("="*60)
print("QUICK TOKEN GENERATOR")
print("="*60)

# Create token payload
now = datetime.utcnow()
expire = now + timedelta(days=8)

payload = {
    "sub": user_id,  # Use user ID, not email, to match production behavior
    "user_id": user_id,
    "exp": int(expire.timestamp()),
    "iat": int(now.timestamp()),
    "jti": str(uuid.uuid4())
}

# Simple JWT implementation
def encode_jwt(payload, secret):
    # Header
    header = {"alg": "HS256", "typ": "JWT"}
    
    # Encode header and payload
    header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b'=').decode()
    payload_encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
    
    # Create signature
    message = f"{header_encoded}.{payload_encoded}"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    signature_encoded = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
    
    # Combine all parts
    return f"{header_encoded}.{payload_encoded}.{signature_encoded}"

# Generate token
token = encode_jwt(payload, SECRET_KEY)

print(f"\nEmail: {email}")
print(f"User ID: {user_id} (dummy)")
print(f"\nToken generated!")

# Create HTML file
html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Quick Login</title>
    <meta charset="UTF-8">
    <style>
        body {{ 
            font-family: Arial; 
            padding: 50px; 
            background: #f0f0f0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 600px;
            width: 100%;
        }}
        button {{ 
            background: #007bff; 
            color: white; 
            border: none; 
            padding: 15px 30px; 
            font-size: 18px; 
            border-radius: 5px; 
            cursor: pointer;
            width: 100%;
            margin: 10px 0;
        }}
        button:hover {{ 
            background: #0056b3; 
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffeeba;
            color: #856404;
            padding: 10px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        code {{
            background: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Quick Login for {email}</h1>
        
        <div class="warning">
            ⚠️ This uses a dummy user ID. You may need to check the actual user ID in your database.
        </div>
        
        <button onclick="loginMethod1()">Method 1: Direct Login</button>
        <button onclick="loginMethod2()">Method 2: Via OAuth Callback</button>
        
        <h3>Or use console (F12):</h3>
        <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
localStorage.setItem('access_token', '{token[:50]}...');
window.location.href = '/dashboard';</pre>
        
        <p>Full token has been logged to console.</p>
    </div>
    
    <script>
        const token = `{token}`;
        console.log('Token:', token);
        
        function loginMethod1() {{
            localStorage.setItem('access_token', token);
            window.location.href = 'http://localhost:3000/dashboard';
        }}
        
        function loginMethod2() {{
            // Try OAuth callback style
            window.location.href = 'http://localhost:3000/auth/callback?token=' + encodeURIComponent(token);
        }}
    </script>
</body>
</html>"""

with open('quick_login.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n✅ Created quick_login.html")
print(f"\nTo login:")
print(f"1. Open in browser: {os.path.abspath('quick_login.html')}")
print(f"2. Click one of the login buttons")
print(f"\nNote: This uses a dummy user ID. If it doesn't work, you'll need to find the actual user ID from your database.")

# Also print the token for manual use
print(f"\nToken (for manual use):")
print(token)

import os