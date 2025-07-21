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
    engine = create_async_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
    
    # Add email_verification_token column
    async with engine.connect() as conn:
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR
            """))
            print("✅ Added/verified email_verification_token column")
        except Exception as e:
            print(f"❌ Error with email_verification_token: {e}")
    
    # Add email_verification_sent_at column
    async with engine.connect() as conn:
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS email_verification_sent_at TIMESTAMP WITH TIME ZONE
            """))
            print("✅ Added/verified email_verification_sent_at column")
        except Exception as e:
            print(f"❌ Error with email_verification_sent_at: {e}")
    
    # Verify columns exist
    async with engine.connect() as conn:
        try:
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('email_verification_token', 'email_verification_sent_at')
            """))
            
            columns = [row[0] for row in result]
            print(f"\n✅ Verified columns exist: {columns}")
        except Exception as e:
            print(f"❌ Error verifying columns: {e}")
    
    await engine.dispose()
    print("\n🎉 Database fix completed!")

if __name__ == "__main__":
    asyncio.run(add_columns())