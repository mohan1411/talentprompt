#!/usr/bin/env python3
"""Find actual user ID and create login page."""

import subprocess
import sys

print("="*60)
print("FIND USER AND CREATE LOGIN")
print("="*60)

# First, let's get the actual user ID using psql
print("\n1. Finding user in database...")

# Database connection parameters
db_commands = [
    # Try different ways to connect
    "psql -U promtitude -d promtitude -h localhost -p 5433 -c \"SELECT id, email, full_name FROM users WHERE email = 'promtitude@gmail.com';\"",
    "psql postgresql://promtitude:promtitude123@localhost:5433/promtitude -c \"SELECT id, email, full_name FROM users WHERE email = 'promtitude@gmail.com';\"",
]

user_id = None
for cmd in db_commands:
    try:
        print(f"\nTrying: {cmd[:50]}...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            print("Output:", result.stdout)
            # Parse the output to find user ID
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'promtitude@gmail.com' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        user_id = parts[0].strip()
                        print(f"\n✅ Found user ID: {user_id}")
                        break
            if user_id:
                break
    except Exception as e:
        print(f"Error: {e}")

if not user_id:
    print("\n❌ Could not find user ID automatically.")
    print("\nPlease run this SQL query manually in your database:")
    print("SELECT id FROM users WHERE email = 'promtitude@gmail.com';")
    user_id = input("\nEnter the user ID you found: ").strip()

if user_id:
    # Now generate the token with the actual user ID
    print(f"\n2. Generating token for user ID: {user_id}")
    
    # Create a Python script that generates the token
    token_script = f"""
import json
import base64
import hmac
import hashlib
from datetime import datetime, timedelta
import uuid

SECRET_KEY = "your-super-secret-key-min-32-chars-long-change-this"
email = "promtitude@gmail.com"
user_id = "{user_id}"

now = datetime.utcnow()
expire = now + timedelta(days=8)

payload = {{
    "sub": user_id,  # Use user ID, not email, to match production behavior
    "user_id": user_id,
    "exp": int(expire.timestamp()),
    "iat": int(now.timestamp()),
    "jti": str(uuid.uuid4())
}}

def encode_jwt(payload, secret):
    header = {{"alg": "HS256", "typ": "JWT"}}
    header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b'=').decode()
    payload_encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
    message = f"{{header_encoded}}.{{payload_encoded}}"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    signature_encoded = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
    return f"{{header_encoded}}.{{payload_encoded}}.{{signature_encoded}}"

token = encode_jwt(payload, SECRET_KEY)
print(token)
"""
    
    # Execute the script to get the token
    result = subprocess.run([sys.executable, '-c', token_script], capture_output=True, text=True)
    if result.returncode == 0:
        token = result.stdout.strip()
        
        # Create the final HTML file
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Login as promtitude@gmail.com</title>
    <style>
        body {{ font-family: Arial; padding: 50px; background: #f0f0f0; }}
        .container {{ background: white; padding: 40px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
        button {{ background: #28a745; color: white; border: none; padding: 15px 30px; font-size: 18px; border-radius: 5px; cursor: pointer; width: 100%; margin: 10px 0; }}
        button:hover {{ background: #218838; }}
        .info {{ background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .token-preview {{ background: #f8f9fa; padding: 10px; border-radius: 5px; word-break: break-all; font-family: monospace; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✅ Login Ready!</h1>
        
        <div class="info">
            <strong>Email:</strong> promtitude@gmail.com<br>
            <strong>User ID:</strong> {user_id}<br>
            <strong>Token:</strong> Valid for 8 days
        </div>
        
        <button onclick="login()">Login to Promtitude Dashboard</button>
        
        <p>Token preview (first 50 chars):</p>
        <div class="token-preview">{token[:50]}...</div>
    </div>
    
    <script>
        const token = `{token}`;
        
        function login() {{
            // Store token in localStorage
            localStorage.setItem('access_token', token);
            
            // Redirect to dashboard
            alert('Token set! Redirecting to dashboard...');
            window.location.href = 'http://localhost:3000/dashboard';
        }}
        
        console.log('Token is ready. Click the button to login.');
    </script>
</body>
</html>"""
        
        with open('login_ready.html', 'w') as f:
            f.write(html)
        
        print(f"\n✅ Success! Created login_ready.html")
        print(f"\n3. To login:")
        print(f"   Open this file in your browser:")
        print(f"   D:\\Projects\\AI\\BusinessIdeas\\SmallBusiness\\TalentPrompt\\backend\\scripts\\login_ready.html")
        print(f"\n   Then click the green 'Login to Promtitude Dashboard' button")
    else:
        print(f"\n❌ Error generating token: {result.stderr}")
else:
    print("\n❌ Cannot proceed without user ID")