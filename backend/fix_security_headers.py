#!/usr/bin/env python3
"""
Fix security headers middleware in main.py
"""

import os
import re

def fix_main_py():
    """Fix the security headers middleware in main.py."""
    
    main_py = "app/main.py"
    if not os.path.exists(main_py):
        print("[ERROR] app/main.py not found")
        return False
    
    with open(main_py, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the problematic line
    old_line = 'response.headers.pop("server", None)'
    new_line = '# Server header removal handled by framework'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        print("[OK] Fixed server header removal")
    
    # Alternative: Look for the entire security headers function and replace it
    if "def add_security_headers" in content:
        # Replace the entire function with a corrected version
        pattern = r'@app\.middleware\("http"\)\s*\nasync def add_security_headers\(request: Request, call_next\):.*?return response'
        
        new_function = '''@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # HSTS for production
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.google.com https://www.gstatic.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://www.google.com; "
        "frame-src 'self' https://www.google.com; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )
    response.headers["Content-Security-Policy"] = csp
    
    # Note: Server header cannot be removed via middleware in FastAPI
    # It's set by the ASGI server (uvicorn) - use --header server:Promtitude when running uvicorn
    
    # Cache control for auth endpoints
    if request.url.path.startswith("/api/v1/auth"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    return response'''
        
        # Try to replace the function
        new_content = re.sub(pattern, new_function, content, flags=re.DOTALL)
        if new_content != content:
            content = new_content
            print("[OK] Replaced entire security headers function")
    
    # Write back the fixed content
    with open(main_py, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] Security headers middleware fixed")
    return True

def create_minimal_security_headers():
    """Create a minimal version if needed."""
    
    minimal = '''# Add this to your main.py after CORS middleware if the full version doesn't work

@app.middleware("http")
async def add_basic_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Basic security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response
'''
    
    with open("minimal_security_headers.txt", "w") as f:
        f.write(minimal)
    
    print("[OK] Created minimal_security_headers.txt as backup")

def main():
    print("Fixing security headers middleware...")
    print("=" * 50)
    
    if not os.path.exists("app/main.py"):
        print("[ERROR] Please run this from the backend directory")
        return False
    
    success = fix_main_py()
    create_minimal_security_headers()
    
    if success:
        print("\n[SUCCESS] Security headers fixed!")
        print("\nRestart your server: uvicorn app.main:app --reload")
        print("\nNote: To remove the 'Server' header, run uvicorn with:")
        print('  uvicorn app.main:app --header "server:Promtitude"')
    
    return success

if __name__ == "__main__":
    main()