"""Clean up any existing enum types before running migrations."""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

async def clean_enums():
    load_dotenv()
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in .env file!")
        return
        
    # Fix URL for asyncpg
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    print("Checking for existing enum types...")
    
    try:
        engine = create_async_engine(database_url)
        
        async with engine.connect() as conn:
            # Check existing enum types
            result = await conn.execute(text("""
                SELECT typname 
                FROM pg_type 
                WHERE typtype = 'e'
                AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                ORDER BY typname;
            """))
            
            enums = [row[0] for row in result]
            
            if enums:
                print(f"Found {len(enums)} enum types:")
                for enum in enums:
                    print(f"  - {enum}")
                
                # Clean up specific enums that might conflict
                conflicting_enums = ['importsource', 'importstatus', 'messagestyle', 'messagestatus']
                for enum in conflicting_enums:
                    if enum in enums:
                        print(f"Dropping enum type: {enum}")
                        await conn.execute(text(f"DROP TYPE IF EXISTS {enum} CASCADE"))
                        await conn.commit()
            else:
                print("No enum types found.")
                
        await engine.dispose()
        print("✅ Enum cleanup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(clean_enums())