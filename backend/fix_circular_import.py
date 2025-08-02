#!/usr/bin/env python3
"""
Fix circular import issue with rate limiter
"""

import os
import re

def fix_main_py():
    """Update main.py to import limiter from core.limiter."""
    
    main_py = "app/main.py"
    if not os.path.exists(main_py):
        print(f"❌ {main_py} not found")
        return False
    
    with open(main_py, 'r') as f:
        content = f.read()
    
    # Replace the limiter initialization with import
    old_limiter = """# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)"""
    
    new_limiter = """# Import shared limiter instance
from app.core.limiter import limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)"""
    
    if old_limiter in content:
        content = content.replace(old_limiter, new_limiter)
        print("✓ Updated main.py to use shared limiter")
    else:
        # Try alternative pattern
        if "limiter = Limiter" in content:
            content = re.sub(
                r'limiter = Limiter\(key_func=get_remote_address\)',
                'from app.core.limiter import limiter',
                content
            )
            print("✓ Updated main.py to use shared limiter (alternative pattern)")
    
    # Also update the imports to remove Limiter if it's not used elsewhere
    content = content.replace(
        "from slowapi import Limiter, _rate_limit_exceeded_handler",
        "from slowapi import _rate_limit_exceeded_handler"
    )
    
    with open(main_py, 'w') as f:
        f.write(content)
    
    return True

def fix_auth_py():
    """Update auth.py to import limiter from core.limiter."""
    
    auth_py = "app/api/v1/endpoints/auth.py"
    if not os.path.exists(auth_py):
        print(f"❌ {auth_py} not found")
        return False
    
    with open(auth_py, 'r') as f:
        content = f.read()
    
    # Replace the import
    old_import = """# Import limiter from main app
from app.main import limiter"""
    
    new_import = """# Import shared limiter instance
from app.core.limiter import limiter"""
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        print("✓ Updated auth.py to use shared limiter")
    elif "from app.main import limiter" in content:
        content = content.replace(
            "from app.main import limiter",
            "from app.core.limiter import limiter"
        )
        print("✓ Updated auth.py to use shared limiter (simple pattern)")
    else:
        # Add the import if it doesn't exist
        if "from app.core.limiter import limiter" not in content:
            # Add after logger definition
            content = content.replace(
                "logger = logging.getLogger(__name__)",
                """logger = logging.getLogger(__name__)

# Import shared limiter instance
from app.core.limiter import limiter"""
            )
            print("✓ Added limiter import to auth.py")
    
    with open(auth_py, 'w') as f:
        f.write(content)
    
    return True

def main():
    print("🔧 Fixing circular import issue...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app/main.py"):
        print("❌ Please run this from the backend directory")
        return False
    
    # Check if slowapi is installed
    try:
        import slowapi
    except ImportError:
        print("❌ slowapi not installed. Run: pip install slowapi")
        return False
    
    # Fix both files
    success = True
    success &= fix_main_py()
    success &= fix_auth_py()
    
    if success:
        print("\n✅ Circular import issue fixed!")
        print("\nNow you can:")
        print("1. Restart your server: uvicorn app.main:app --reload")
        print("2. Run security tests: python test_security.py")
    else:
        print("\n❌ Failed to fix circular import issue")
    
    return success

if __name__ == "__main__":
    main()