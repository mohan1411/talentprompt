#!/usr/bin/env python3
"""
Script to add rate limiting to auth endpoints
Run this after add_security_features.py: python add_auth_rate_limiting.py
"""

import re
import os
import sys


def add_limiter_import(content):
    """Add limiter import to auth.py."""
    if "from slowapi import limiter" in content:
        print("✓ Limiter already imported")
        return content
    
    # Add after the router import
    router_import = "router = APIRouter()"
    if router_import in content:
        new_import = """router = APIRouter()
logger = logging.getLogger(__name__)

# Import limiter from main app
from app.main import limiter"""
        
        content = content.replace(
            "router = APIRouter()\nlogger = logging.getLogger(__name__)",
            new_import
        )
        print("✓ Added limiter import")
    
    return content


def add_rate_limit_to_endpoint(content, endpoint_name, pattern, limit):
    """Add rate limiting to a specific endpoint."""
    
    # Check if already has rate limiting
    if f'@limiter.limit("{limit}")' in content:
        print(f"✓ {endpoint_name} already has rate limiting")
        return content
    
    # Find the endpoint
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        # Insert rate limit decorator before the endpoint
        decorator = f'@limiter.limit("{limit}")\n'
        insert_pos = match.start()
        content = content[:insert_pos] + decorator + content[insert_pos:]
        print(f"✓ Added rate limiting to {endpoint_name}: {limit}")
    else:
        print(f"⚠ Could not find {endpoint_name} endpoint")
    
    return content


def process_auth_py():
    """Process the auth.py file to add rate limiting."""
    
    auth_py_path = "app/api/v1/endpoints/auth.py"
    
    if not os.path.exists(auth_py_path):
        print(f"❌ Error: {auth_py_path} not found.")
        return False
    
    # Read the current content
    with open(auth_py_path, 'r') as f:
        content = f.read()
    
    # Backup the original file
    backup_path = auth_py_path + '.backup'
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"✓ Created backup at {backup_path}")
    
    # Add limiter import
    content = add_limiter_import(content)
    
    # Add rate limiting to endpoints
    endpoints = [
        ("login", r'^@router\.post\("/login"', "5/minute"),
        ("register", r'^@router\.post\("/register"', "3/hour"),
        ("verify-email", r'^@router\.post\("/verify-email"', "10/hour"),
        ("resend-verification", r'^@router\.post\("/resend-verification"', "3/hour"),
        ("generate-extension-token", r'^@router\.post\("/generate-extension-token"', "5/hour"),
    ]
    
    for endpoint_name, pattern, limit in endpoints:
        content = add_rate_limit_to_endpoint(content, endpoint_name, pattern, limit)
    
    # Write the updated content
    with open(auth_py_path, 'w') as f:
        f.write(content)
    
    print("\n✅ Rate limiting added to auth endpoints!")
    return True


def create_rate_limit_test_script():
    """Create a script to test rate limiting."""
    test_script = '''#!/bin/bash
# Test rate limiting on various endpoints

echo "Testing rate limiting on login endpoint (5/minute limit)..."
for i in {1..7}; do
    echo "Attempt $i:"
    curl -X POST http://localhost:8000/api/v1/auth/login \\
        -H "Content-Type: application/json" \\
        -d \'{"username":"test@example.com","password":"wrongpass"}\' \\
        -w "\\nStatus: %{http_code}\\n"
    sleep 1
done

echo "\\nTesting rate limiting on register endpoint (3/hour limit)..."
for i in {1..5}; do
    echo "Attempt $i:"
    curl -X POST http://localhost:8000/api/v1/auth/register \\
        -H "Content-Type: application/json" \\
        -d \'{"email":"test'$i'@example.com","username":"test'$i'","password":"TestPass123!"}\' \\
        -w "\\nStatus: %{http_code}\\n"
    sleep 1
done

echo "\\nRate limiting test complete!"
echo "You should see 429 (Too Many Requests) status codes after the limits are exceeded."
'''
    
    with open("test_rate_limiting.sh", "w") as f:
        f.write(test_script)
    os.chmod("test_rate_limiting.sh", 0o755)
    print("✓ Created test_rate_limiting.sh script")


if __name__ == "__main__":
    print("🔒 Auth Rate Limiting Enhancement Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app/api/v1/endpoints/auth.py"):
        print("❌ Error: This script must be run from the backend directory")
        print("   Current directory:", os.getcwd())
        sys.exit(1)
    
    # Check if slowapi is in requirements
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r") as f:
            if "slowapi" not in f.read():
                print("⚠ Warning: slowapi not found in requirements.txt")
                print("  Run: pip install slowapi && pip freeze | grep slowapi >> requirements.txt")
    
    # Process the auth.py file
    success = process_auth_py()
    
    if success:
        create_rate_limit_test_script()
        print("\n✨ Auth rate limiting complete!")
        print("\n📋 Test the rate limiting:")
        print("   ./test_rate_limiting.sh")
    else:
        print("\n❌ Rate limiting enhancement failed.")