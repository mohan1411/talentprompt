#!/usr/bin/env python3
"""Debug environment variables."""

import os
import sys

print("=== Environment Debug ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print("\n=== Database Configuration ===")

# Check for DATABASE_URL
db_url = os.environ.get('DATABASE_URL', 'NOT SET')
if db_url != 'NOT SET':
    # Hide password for security
    import re
    safe_url = re.sub(r'://[^@]+@', '://***:***@', db_url)
    print(f"DATABASE_URL: {safe_url}")
else:
    print("DATABASE_URL: NOT SET ⚠️")

# Check for individual postgres vars
print(f"POSTGRES_SERVER: {os.environ.get('POSTGRES_SERVER', 'NOT SET')}")
print(f"POSTGRES_USER: {os.environ.get('POSTGRES_USER', 'NOT SET')}")
print(f"POSTGRES_PASSWORD: {'SET' if os.environ.get('POSTGRES_PASSWORD') else 'NOT SET'}")
print(f"POSTGRES_DB: {os.environ.get('POSTGRES_DB', 'NOT SET')}")

# Check other important vars
print("\n=== Other Configuration ===")
print(f"SECRET_KEY: {'SET' if os.environ.get('SECRET_KEY') else 'NOT SET'}")
print(f"FIRST_SUPERUSER: {os.environ.get('FIRST_SUPERUSER', 'NOT SET')}")
print(f"BACKEND_CORS_ORIGINS: {os.environ.get('BACKEND_CORS_ORIGINS', 'NOT SET')}")
print(f"INIT_DB: {os.environ.get('INIT_DB', 'NOT SET')}")
print(f"PORT: {os.environ.get('PORT', 'NOT SET')}")
print(f"RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT', 'NOT SET')}")

# Try to load settings
print("\n=== Loading Settings ===")
try:
    from app.core.config import settings
    print(f"Settings loaded successfully")
    print(f"DATABASE_URL from settings: {settings.DATABASE_URL[:30]}..." if settings.DATABASE_URL else "DATABASE_URL not in settings")
except Exception as e:
    print(f"Error loading settings: {e}")

print("\n=== End Debug ===")