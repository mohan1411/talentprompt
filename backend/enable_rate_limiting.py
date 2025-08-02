#!/usr/bin/env python3
"""Enable rate limiting in a simple way"""

import os

def add_to_main():
    """Add rate limiting to main.py"""
    
    # Check if slowapi is installed
    try:
        import slowapi
    except ImportError:
        print("ERROR: slowapi not installed!")
        print("Run: pip install slowapi")
        return False
    
    main_py = "app/main.py"
    with open(main_py, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if already has limiter
    if "from app.core.limiter import limiter" in content:
        print("✓ Rate limiter already imported in main.py")
        return True
    
    # Add after the analytics middleware line
    if "app.add_middleware(AnalyticsMiddleware)" in content:
        new_content = content.replace(
            "app.add_middleware(AnalyticsMiddleware)",
            """app.add_middleware(AnalyticsMiddleware)

# Add rate limiting
from app.core.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)"""
        )
        
        with open(main_py, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        print("✓ Added rate limiter to main.py")
        return True
    
    return False

def add_to_auth():
    """Add simple rate limiting to login endpoint only"""
    
    auth_py = "app/api/v1/endpoints/auth.py"
    with open(auth_py, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if already has rate limiting
    if "@limiter.limit" in content:
        print("✓ Rate limiting already present in auth.py")
        return True
    
    # Add import if needed
    if "from app.core.limiter import limiter" not in content:
        # Add after the router line
        content = content.replace(
            "router = APIRouter()",
            """router = APIRouter()

# Import rate limiter
from app.core.limiter import limiter
from fastapi import Request"""
        )
    
    # Add rate limiting to login endpoint
    content = content.replace(
        '@router.post("/login", response_model=Token)\nasync def login(',
        '''@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,'''
    )
    
    with open(auth_py, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✓ Added rate limiting to login endpoint")
    return True

def main():
    print("Enabling rate limiting...")
    
    # Ensure limiter.py exists
    if not os.path.exists("app/core/limiter.py"):
        print("✗ app/core/limiter.py missing - creating it...")
        os.makedirs("app/core", exist_ok=True)
        with open("app/core/limiter.py", "w", encoding="utf-8") as f:
            f.write('''"""Rate limiter instance"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
''')
        print("✓ Created app/core/limiter.py")
    
    # Add to main.py
    add_to_main()
    
    # Add to auth.py
    add_to_auth()
    
    print("\n✓ Rate limiting enabled!")
    print("Restart your server for changes to take effect")

if __name__ == "__main__":
    main()