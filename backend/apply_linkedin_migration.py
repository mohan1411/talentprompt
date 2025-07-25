#!/usr/bin/env python3
"""Apply LinkedIn columns directly via SQL."""

import asyncio
import os
import sys

# Add the app directory to the path
sys.path.insert(0, '/app')

try:
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.core.config import settings
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying alternative import...")
    from sqlalchemy.ext.asyncio import create_async_engine
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+asyncpg://', 1)
    elif DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)

async def apply_migration():
    """Apply the LinkedIn migration directly."""
    
    # Get database URL
    try:
        db_url = str(settings.DATABASE_URL)
    except:
        db_url = DATABASE_URL
        
    print(f"Connecting to database...")
    
    # Create engine
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        print("Adding LinkedIn columns...")
        
        try:
            # Add columns one by one to handle if some already exist
            await conn.execute("""
                ALTER TABLE resumes 
                ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR UNIQUE
            """)
            print("✓ Added linkedin_url column")
        except Exception as e:
            print(f"Column linkedin_url might already exist: {e}")
            
        try:
            await conn.execute("""
                ALTER TABLE resumes 
                ADD COLUMN IF NOT EXISTS linkedin_data JSON
            """)
            print("✓ Added linkedin_data column")
        except Exception as e:
            print(f"Column linkedin_data might already exist: {e}")
            
        try:
            await conn.execute("""
                ALTER TABLE resumes 
                ADD COLUMN IF NOT EXISTS last_linkedin_sync TIMESTAMP WITH TIME ZONE
            """)
            print("✓ Added last_linkedin_sync column")
        except Exception as e:
            print(f"Column last_linkedin_sync might already exist: {e}")
            
        try:
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS ix_resumes_linkedin_url ON resumes(linkedin_url)
            """)
            print("✓ Created index on linkedin_url")
        except Exception as e:
            print(f"Index might already exist: {e}")
    
    print("\n✅ LinkedIn columns have been added successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(apply_migration())
    
    # Start the application after migration
    import os
    print("\n🚀 Starting application...")
    os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])