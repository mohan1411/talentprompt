#!/usr/bin/env python3
"""Check if rate limiting is configured in the code"""

import os

def check_files():
    # Check main.py
    print("Checking main.py for rate limiter setup...")
    if os.path.exists("app/main.py"):
        with open("app/main.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "limiter" in content and "Limiter" in content:
                print("✓ Rate limiter found in main.py")
                if "app.state.limiter" in content:
                    print("✓ Limiter attached to app state")
            else:
                print("✗ Rate limiter NOT found in main.py")
    
    # Check auth.py
    print("\nChecking auth.py for rate limit decorators...")
    if os.path.exists("app/api/v1/endpoints/auth.py"):
        with open("app/api/v1/endpoints/auth.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "@limiter.limit" in content:
                print("✓ Rate limit decorators found in auth.py")
                # Count how many
                count = content.count("@limiter.limit")
                print(f"  Found {count} rate limited endpoints")
            else:
                print("✗ No rate limit decorators in auth.py")
    
    # Check if limiter.py exists
    print("\nChecking for limiter module...")
    if os.path.exists("app/core/limiter.py"):
        print("✓ app/core/limiter.py exists")
    else:
        print("✗ app/core/limiter.py NOT found")

if __name__ == "__main__":
    check_files()