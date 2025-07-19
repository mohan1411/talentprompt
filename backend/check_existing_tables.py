"""Check which outreach tables and types already exist."""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

async def check_existing():
    load_dotenv()
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in .env file!")
        return
        
    # Fix URL for asyncpg
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    try:
        engine = create_async_engine(database_url)
        
        async with engine.connect() as conn:
            # Check for outreach tables
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('outreach_messages', 'outreach_templates')
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result]
            
            print("Outreach tables:")
            if tables:
                for table in tables:
                    print(f"  ✓ {table} exists")
            else:
                print("  ✗ No outreach tables found")
            
            # Check for enum types
            result = await conn.execute(text("""
                SELECT typname 
                FROM pg_type 
                WHERE typtype = 'e'
                AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                AND typname IN ('messagestyle', 'messagestatus')
                ORDER BY typname;
            """))
            
            enums = [row[0] for row in result]
            
            print("\nOutreach enum types:")
            if enums:
                for enum in enums:
                    print(f"  ✓ {enum} exists")
            else:
                print("  ✗ No outreach enums found")
                
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_existing())