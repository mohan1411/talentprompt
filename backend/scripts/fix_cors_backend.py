#!/usr/bin/env python3
"""Check and fix CORS settings in backend."""

import os
import sys

print("="*60)
print("CORS CONFIGURATION CHECK")
print("="*60)

# Check current environment
print("\n1. Current Environment Variables:")
cors_env = os.environ.get('BACKEND_CORS_ORIGINS', 'Not set')
print(f"   BACKEND_CORS_ORIGINS: {cors_env}")

print("\n2. To fix CORS issues, restart your backend with:")
print("\nFor Windows (PowerShell):")
print('$env:BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:8000,http://localhost:8080"')
print("cd backend")
print("uvicorn app.main:app --reload --host 0.0.0.0 --port 8001")

print("\nFor Windows (Command Prompt):")
print('set BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8080')
print("cd backend")
print("uvicorn app.main:app --reload --host 0.0.0.0 --port 8001")

print("\n3. Or create a .env file in the backend directory with:")
print("BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8080")

# Create a .env file if it doesn't exist
env_file = os.path.join("..", ".env")
if not os.path.exists(env_file):
    print(f"\n4. Creating {env_file} with proper CORS settings...")
    with open(env_file, 'w') as f:
        f.write("# CORS Settings\n")
        f.write("BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8080\n")
        f.write("\n# Database\n")
        f.write("DATABASE_URL=postgresql://promtitude:promtitude123@localhost:5433/promtitude\n")
        f.write("\n# Other settings\n")
        f.write("SECRET_KEY=your-super-secret-key-min-32-chars-long-change-this\n")
        f.write("FIRST_SUPERUSER=admin@promtitude.com\n")
        f.write("FIRST_SUPERUSER_PASSWORD=changethis\n")
    print("   ✅ Created .env file")
else:
    print(f"\n4. .env file already exists at {os.path.abspath(env_file)}")
    print("   Make sure it includes BACKEND_CORS_ORIGINS")

print("\n" + "="*60)
print("IMPORTANT")
print("="*60)
print("\nAfter updating CORS settings, you MUST restart the backend!")
print("The backend reads these settings only at startup.")