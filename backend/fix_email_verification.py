"""Quick fix to add email verification columns to production database."""

import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

async def add_columns():
    """Add email verification columns to users table."""
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        # Add email_verification_token column
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN email_verification_token VARCHAR
            """))
            print("✅ Added email_verification_token column")
        except Exception as e:
            if "already exists" in str(e):
                print("⚠️  email_verification_token column already exists")
            else:
                print(f"❌ Error adding email_verification_token: {e}")
        
        # Add email_verification_sent_at column
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN email_verification_sent_at TIMESTAMP WITH TIME ZONE
            """))
            print("✅ Added email_verification_sent_at column")
        except Exception as e:
            if "already exists" in str(e):
                print("⚠️  email_verification_sent_at column already exists")
            else:
                print(f"❌ Error adding email_verification_sent_at: {e}")
        
        # Verify columns exist
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('email_verification_token', 'email_verification_sent_at')
        """))
        
        columns = [row[0] for row in result]
        print(f"\n✅ Verified columns exist: {columns}")
    
    await engine.dispose()
    print("\n🎉 Database fix completed!")

if __name__ == "__main__":
    asyncio.run(add_columns())