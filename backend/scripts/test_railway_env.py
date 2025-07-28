#!/usr/bin/env python3
"""Test Railway environment and database connection."""

import os
import sys

print("="*60, flush=True)
print("RAILWAY ENVIRONMENT TEST", flush=True)
print("="*60, flush=True)

# Check Python version
print(f"\n1. Python version: {sys.version}", flush=True)

# Check current directory
print(f"\n2. Current directory: {os.getcwd()}", flush=True)

# Check if file exists
import_file = "promtitude_95_resumes_export.json"
print(f"\n3. Import file exists: {os.path.exists(import_file)}", flush=True)
if os.path.exists(import_file):
    print(f"   File size: {os.path.getsize(import_file)} bytes", flush=True)

# Check environment variables
print(f"\n4. Environment variables:", flush=True)
print(f"   DATABASE_URL: {'Set' if os.getenv('DATABASE_URL') else 'Not set'}", flush=True)
print(f"   OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}", flush=True)
print(f"   QDRANT_URL: {'Set' if os.getenv('QDRANT_URL') else 'Not set'}", flush=True)

# Try to import app modules
print(f"\n5. Testing imports:", flush=True)
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.core.config import settings
    print("   ✅ Can import settings", flush=True)
    print(f"   Database URL from settings: {settings.DATABASE_URL[:50]}..." if settings.DATABASE_URL else "   No DATABASE_URL in settings", flush=True)
except Exception as e:
    print(f"   ❌ Cannot import settings: {e}", flush=True)

# Test database connection
print(f"\n6. Testing database connection:", flush=True)
try:
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine
    
    async def test_db():
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            print("   ✅ Database connection successful", flush=True)
    
    asyncio.run(test_db())
except Exception as e:
    print(f"   ❌ Database connection failed: {e}", flush=True)

print("\n" + "="*60, flush=True)
print("TEST COMPLETE", flush=True)
print("="*60, flush=True)