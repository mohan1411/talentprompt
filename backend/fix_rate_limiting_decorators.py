#!/usr/bin/env python3
"""
Fix rate limiting decorators to include request parameter
"""

import os
import re

def fix_auth_endpoints():
    """Fix auth endpoints to include request parameter for rate limiting."""
    
    auth_py = "app/api/v1/endpoints/auth.py"
    if not os.path.exists(auth_py):
        print(f"❌ {auth_py} not found")
        return False
    
    with open(auth_py, 'r') as f:
        content = f.read()
    
    # Define endpoints that need fixing
    endpoints_to_fix = [
        {
            'name': 'register',
            'old': '@limiter.limit("3/hour")\n@router.post("/register", response_model=UserSchema)\nasync def register(',
            'new': '@router.post("/register", response_model=UserSchema)\n@limiter.limit("3/hour")\nasync def register(\n    request: Request,'
        },
        {
            'name': 'login',
            'old': '@limiter.limit("5/minute")\n@router.post("/login", response_model=Token)\nasync def login(',
            'new': '@router.post("/login", response_model=Token)\n@limiter.limit("5/minute")\nasync def login(\n    request: Request,'
        },
        {
            'name': 'verify_email',
            'old': '@limiter.limit("10/hour")\n@router.post("/verify-email")\nasync def verify_email(',
            'new': '@router.post("/verify-email")\n@limiter.limit("10/hour")\nasync def verify_email(\n    request: Request,'
        },
        {
            'name': 'resend_verification',
            'old': '@limiter.limit("3/hour")\n@router.post("/resend-verification")\nasync def resend_verification(',
            'new': '@router.post("/resend-verification")\n@limiter.limit("3/hour")\nasync def resend_verification(\n    request: Request,'
        }
    ]
    
    # First, ensure Request is imported
    if "from fastapi import" in content and ", Request" not in content:
        # Add Request to the fastapi imports
        content = re.sub(
            r'(from fastapi import[^)]+)([\)])',
            r'\1, Request\2',
            content
        )
        print("✓ Added Request to imports")
    
    # Apply fixes for each endpoint
    for endpoint in endpoints_to_fix:
        if endpoint['old'] in content:
            content = content.replace(endpoint['old'], endpoint['new'])
            print(f"✓ Fixed {endpoint['name']} endpoint")
        else:
            # Try to fix manually by finding the pattern
            pattern = rf"(@limiter\.limit\([^)]+\)\s*\n)?(@router\.(post|get)\([^)]+\)\s*\n)async def {endpoint['name']}\("
            
            def replacer(match):
                limiter_dec = match.group(1) or ''
                router_dec = match.group(2)
                # Put router decorator first, then limiter
                return f"{router_dec}{limiter_dec}async def {endpoint['name']}(\n    request: Request,"
            
            new_content = re.sub(pattern, replacer, content, flags=re.MULTILINE)
            if new_content != content:
                content = new_content
                print(f"✓ Fixed {endpoint['name']} endpoint (pattern match)")
    
    # Write the fixed content
    with open(auth_py, 'w') as f:
        f.write(content)
    
    return True

def create_simple_fix():
    """Create a simple script to remove rate limiting if needed."""
    
    simple_fix = '''#!/usr/bin/env python3
"""
Simple script to temporarily disable rate limiting
"""

import re

with open("app/api/v1/endpoints/auth.py", "r") as f:
    content = f.read()

# Remove all rate limiting decorators
content = re.sub(r'@limiter\.limit\([^)]+\)\s*\n', '', content)

# Remove limiter import
content = re.sub(r'.*from app\.core\.limiter import limiter.*\n', '', content)

with open("app/api/v1/endpoints/auth.py", "w") as f:
    f.write(content)

print("✓ Rate limiting temporarily disabled")
'''
    
    with open("disable_rate_limiting.py", "w") as f:
        f.write(simple_fix)
    
    print("✓ Created disable_rate_limiting.py as a fallback option")

def main():
    print("🔧 Fixing rate limiting decorators...")
    print("=" * 50)
    
    if not os.path.exists("app/api/v1/endpoints/auth.py"):
        print("❌ Please run this from the backend directory")
        return False
    
    success = fix_auth_endpoints()
    create_simple_fix()
    
    if success:
        print("\n✅ Rate limiting decorators fixed!")
        print("\nNow restart your server: uvicorn app.main:app --reload")
        print("\nIf you still have issues, you can temporarily disable rate limiting:")
        print("  python disable_rate_limiting.py")
    
    return success

if __name__ == "__main__":
    main()