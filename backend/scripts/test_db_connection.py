#!/usr/bin/env python3
"""Test database connection in Railway."""

import os
import asyncio
import sys

print("Testing Railway Database Connection")
print("="*60)

# Check environment
print(f"1. DATABASE_URL from env: {os.getenv('DATABASE_URL', 'NOT SET')}")
print(f"2. Current directory: {os.getcwd()}")
print(f"3. Python path: {sys.path[:2]}")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import settings
try:
    from app.core.config import settings
    print(f"4. DATABASE_URL from settings: {settings.DATABASE_URL}")
    
    # Parse the URL
    db_url = str(settings.DATABASE_URL)
    if "railway.internal" in db_url:
        print("   ⚠️  Using internal Railway URL")
    else:
        print("   ✅ Using public URL")
        
except Exception as e:
    print(f"4. Failed to import settings: {e}")
    sys.exit(1)

# Test connection
async def test_connection():
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        
        # Try with the settings URL
        print("\n5. Testing database connection...")
        engine = create_async_engine(str(settings.DATABASE_URL))
        
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            print("   ✅ Database connection successful!")
            
            # Check if tables exist
            result = await conn.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('users', 'resumes')
            """)
            count = result.scalar()
            print(f"   ✅ Found {count} required tables")
            
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        
        # Try alternative connection
        if os.getenv('DATABASE_URL'):
            print("\n6. Trying with direct env var...")
            try:
                engine2 = create_async_engine(os.getenv('DATABASE_URL'))
                async with engine2.connect() as conn:
                    await conn.execute("SELECT 1")
                    print("   ✅ Direct env connection works!")
            except Exception as e2:
                print(f"   ❌ Direct env also failed: {e2}")

if __name__ == "__main__":
    asyncio.run(test_connection())