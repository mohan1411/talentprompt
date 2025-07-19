"""Check current migration status."""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

async def check_migrations():
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
            # Check if alembic_version table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'alembic_version'
                );
            """))
            exists = result.scalar()
            
            if not exists:
                print("⚠️  No alembic_version table found. No migrations have been run yet.")
                print("Run: alembic upgrade head")
            else:
                # Get current revision
                result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar()
                
                if version:
                    print(f"✅ Current migration version: {version}")
                else:
                    print("⚠️  alembic_version table exists but is empty")
                    
                # Check which tables exist
                result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """))
                
                tables = [row[0] for row in result]
                print(f"\nExisting tables ({len(tables)}):")
                for table in tables:
                    print(f"  - {table}")
                    
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_migrations())