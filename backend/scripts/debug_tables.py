#!/usr/bin/env python3
"""Debug why tables aren't being created."""

import os
import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def debug_database():
    db_url = os.getenv("DATABASE_URL")
    if not db_url and len(sys.argv) > 1:
        db_url = sys.argv[1]
    
    if not db_url:
        print("Please provide DATABASE_URL")
        return
    
    # Convert to async URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    print("🔍 Debugging Database")
    print("=" * 50)
    
    try:
        engine = create_async_engine(db_url, echo=False)
        
        async with engine.connect() as conn:
            # Check existing tables
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result]
            print(f"\n📋 Existing tables ({len(tables)}):")
            for table in tables:
                print(f"   - {table}")
            
            # Check if our tables exist
            our_tables = ['candidate_submissions', 'invitation_campaigns']
            missing = [t for t in our_tables if t not in tables]
            
            if missing:
                print(f"\n❌ Missing tables: {missing}")
            else:
                print("\n✅ All required tables exist!")
                
            # Check users table structure
            if 'users' in tables:
                result = await conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'id'
                    LIMIT 1;
                """))
                row = result.first()
                if row:
                    print(f"\n👤 users.id type: {row[1]}")
                    
            # Check resumes table
            if 'resumes' in tables:
                result = await conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'resumes' AND column_name = 'id'
                    LIMIT 1;
                """))
                row = result.first()
                if row:
                    print(f"📄 resumes.id type: {row[1]}")
                    
            # Try to create a simple test table
            print("\n🧪 Testing table creation...")
            try:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS test_table_delete_me (
                        id SERIAL PRIMARY KEY,
                        test_column VARCHAR(50)
                    );
                """))
                await conn.commit()
                print("✅ Test table created successfully!")
                
                # Clean up
                await conn.execute(text("DROP TABLE IF EXISTS test_table_delete_me;"))
                await conn.commit()
                print("✅ Test table deleted")
                
            except Exception as e:
                print(f"❌ Cannot create tables: {e}")
                print("\n⚠️  Possible issues:")
                print("1. User doesn't have CREATE permission")
                print("2. Database is read-only")
                print("3. Connection issues")
                
        await engine.dispose()
        
    except Exception as e:
        print(f"\n❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_database())