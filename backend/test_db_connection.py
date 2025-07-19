import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

async def test_connection():
    # Load environment variables
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in .env file!")
        print("Please add your Railway DATABASE_URL to the .env file")
        return
    
    # Ensure asyncpg driver
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://")
    
    print(f"Testing connection to database...")
    print(f"URL pattern: {database_url.split('@')[1] if '@' in database_url else 'Invalid URL'}")
    
    try:
        # Create engine with SSL mode
        engine = create_async_engine(
            database_url,
            echo=True,
            connect_args={
                "server_settings": {"jit": "off"},
                "ssl": "require"  # Railway requires SSL
            }
        )
        
        # Test connection
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            print("✅ Database connection successful!")
            
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check if DATABASE_URL is correct in .env file")
        print("2. Make sure you're using the Railway PostgreSQL URL")
        print("3. Ensure your IP is allowed (check Railway dashboard)")
        
    finally:
        if 'engine' in locals():
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())