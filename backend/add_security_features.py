#!/usr/bin/env python3
"""
Script to add security features to main.py
Run this script from the backend directory: python add_security_features.py
"""

import re
import os
import sys

def add_security_headers_middleware(content):
    """Add security headers middleware to the FastAPI app."""
    
    # Check if security headers already exist
    if "add_security_headers" in content:
        print("✓ Security headers middleware already exists")
        return content
    
    # Find where to insert the security headers middleware (after CORS middleware)
    cors_pattern = r'(app\.add_middleware\(\s*CORSMiddleware[^)]+\))'
    
    security_headers_code = '''

# Security headers middleware
@app.middleware("http")
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
    
    # Remove server header
    response.headers.pop("server", None)
    
    # Cache control for auth endpoints
    if request.url.path.startswith("/api/v1/auth"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    return response'''
    
    # Insert after CORS middleware
    match = re.search(cors_pattern, content, re.DOTALL)
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + security_headers_code + content[insert_pos:]
        print("✓ Added security headers middleware")
    else:
        print("⚠ Could not find CORS middleware, adding security headers at the end of middleware section")
        # Find the last middleware addition
        middleware_pattern = r'(app\.add_middleware\([^)]+\))'
        matches = list(re.finditer(middleware_pattern, content))
        if matches:
            insert_pos = matches[-1].end()
            content = content[:insert_pos] + security_headers_code + content[insert_pos:]
            print("✓ Added security headers middleware")
    
    return content


def add_rate_limiting(content):
    """Add rate limiting to the FastAPI app."""
    
    # Check if rate limiting already exists
    if "slowapi" in content or "Limiter" in content:
        print("✓ Rate limiting already exists")
        return content
    
    # Add imports
    import_section = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware"""
    
    new_imports = """from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded"""
    
    content = content.replace(import_section, new_imports)
    
    # Add limiter initialization after app creation
    app_pattern = r'(app = FastAPI\([^)]+\))'
    
    limiter_code = '''

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)'''
    
    match = re.search(app_pattern, content, re.DOTALL)
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + limiter_code + content[insert_pos:]
        print("✓ Added rate limiter initialization")
    
    # Add rate limiting to login endpoint
    login_pattern = r'(@router\.post\("/login"[^)]*\)\s*async def login)'
    login_replacement = r'@router.post("/login", response_model=Token)\n@limiter.limit("5/minute")\nasync def login'
    
    # Note: You'll need to manually add @limiter.limit decorators to endpoints in auth.py
    print("✓ Rate limiting setup complete")
    print("  ⚠ Remember to add @limiter.limit decorators to sensitive endpoints in auth.py")
    
    return content


def disable_docs_in_production(content):
    """Disable API documentation in production."""
    
    # Check if already disabled
    if 'docs_url=docs_url' in content or 'settings.ENVIRONMENT != "production"' in content:
        print("✓ API docs already conditionally disabled")
        return content
    
    # Find the FastAPI initialization
    app_pattern = r'app = FastAPI\((.*?)\)'
    
    match = re.search(app_pattern, content, re.DOTALL)
    if match:
        # Get the current parameters
        params = match.group(1)
        
        # Add conditional docs before app initialization
        conditional_docs = '''
# Conditionally enable API documentation
docs_url = "/docs" if settings.ENVIRONMENT != "production" else None
redoc_url = "/redoc" if settings.ENVIRONMENT != "production" else None
openapi_url = f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None

app = FastAPI('''
        
        # Replace docs_url and redoc_url parameters
        new_params = re.sub(r'docs_url="/docs"', 'docs_url=docs_url', params)
        new_params = re.sub(r'redoc_url="/redoc"', 'redoc_url=redoc_url', new_params)
        new_params = re.sub(r'openapi_url=f"{settings.API_V1_STR}/openapi.json"', 'openapi_url=openapi_url', new_params)
        
        # Find where app = FastAPI starts
        app_start = content.find('app = FastAPI(')
        if app_start != -1:
            # Insert conditional docs before app initialization
            content = content[:app_start] + conditional_docs + new_params + ')' + content[match.end():]
            print("✓ API documentation disabled in production")
    
    return content


def add_request_import(content):
    """Ensure Request is imported from fastapi."""
    if "from fastapi import" in content and "Request" not in content:
        # Find the fastapi import line
        import_pattern = r'(from fastapi import[^\\n]+)'
        match = re.search(import_pattern, content)
        if match:
            imports = match.group(1)
            if "Request" not in imports:
                # Add Request to imports
                content = content.replace(imports, imports.rstrip() + ", Request")
                print("✓ Added Request import")
    return content


def process_main_py():
    """Process the main.py file to add security features."""
    
    main_py_path = "app/main.py"
    
    if not os.path.exists(main_py_path):
        print(f"❌ Error: {main_py_path} not found. Make sure you're running this from the backend directory.")
        return False
    
    # Read the current content
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Backup the original file
    backup_path = main_py_path + '.backup'
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"✓ Created backup at {backup_path}")
    
    # Apply security enhancements
    content = add_request_import(content)
    content = add_security_headers_middleware(content)
    content = add_rate_limiting(content)
    content = disable_docs_in_production(content)
    
    # Write the updated content
    with open(main_py_path, 'w') as f:
        f.write(content)
    
    print("\n✅ Security features added successfully!")
    print("\n📋 Next steps:")
    print("1. Install rate limiting dependency: pip install slowapi")
    print("2. Add @limiter.limit decorators to auth endpoints in app/api/v1/endpoints/auth.py:")
    print('   - @limiter.limit("5/minute") for login')
    print('   - @limiter.limit("3/hour") for register')
    print('   - @limiter.limit("10/hour") for password reset')
    print("3. Test the changes locally before deploying")
    print("4. Deploy to production with these environment variables:")
    print("   - DEBUG=False")
    print("   - ENVIRONMENT=production")
    print("   - SECRET_KEY=<your-secure-key>")
    
    return True


def create_requirements_addition():
    """Create a file with the new requirement to add."""
    with open("security_requirements.txt", "w") as f:
        f.write("# Add this to your requirements.txt\nslowapi==0.1.9\n")
    print("\n✓ Created security_requirements.txt with the new dependency")


if __name__ == "__main__":
    print("🔒 Promtitude Security Enhancement Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app/main.py"):
        print("❌ Error: This script must be run from the backend directory")
        print("   Current directory:", os.getcwd())
        print("   Please run: cd backend && python add_security_features.py")
        sys.exit(1)
    
    # Process the main.py file
    success = process_main_py()
    
    if success:
        create_requirements_addition()
        print("\n✨ Security enhancements complete!")
    else:
        print("\n❌ Security enhancement failed. Please check the errors above.")