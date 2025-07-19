"""Check the actual enum values in the database."""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

async def check_enums():
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found!")
        return
        
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(database_url)
    
    async with engine.connect() as conn:
        # Check enum values
        result = await conn.execute(text("""
            SELECT 
                t.typname AS enum_name,
                e.enumlabel AS enum_value
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname IN ('messagestyle', 'messagestatus')
            ORDER BY t.typname, e.enumsortorder;
        """))
        
        print("Enum values in database:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")
            
        # Try to recreate with correct values if needed
        result = await conn.execute(text("""
            SELECT enumlabel FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'messagestyle')
        """))
        values = [row[0] for row in result]
        
        if 'CASUAL' in values or 'casual' not in values:
            print("\n⚠️  Enum values are incorrect! Fixing...")
            
            # Drop and recreate
            await conn.execute(text("DROP TYPE IF EXISTS messagestyle CASCADE"))
            await conn.execute(text("DROP TYPE IF EXISTS messagestatus CASCADE"))
            await conn.commit()
            
            # Recreate with correct values
            await conn.execute(text("CREATE TYPE messagestyle AS ENUM ('casual', 'professional', 'technical')"))
            await conn.execute(text("CREATE TYPE messagestatus AS ENUM ('generated', 'sent', 'opened', 'responded', 'not_interested')"))
            await conn.commit()
            
            print("✅ Enums recreated with correct values!")
            
            # Note: This will drop the tables too because of CASCADE
            print("⚠️  You need to recreate the outreach tables now!")
            print("Run: python create_outreach_tables.py")
        else:
            print("\n✅ Enum values are correct!")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_enums())