#!/usr/bin/env python
"""Railway-specific startup script with forced migrations."""
import os
import sys
import subprocess
import asyncio
import uvicorn

def run_migrations():
    """Force run migrations."""
    print("=" * 60)
    print("RUNNING DATABASE MIGRATIONS")
    print("=" * 60)
    
    try:
        # First, show current status
        current = subprocess.run(["alembic", "current"], capture_output=True, text=True)
        print(f"Current revision: {current.stdout}")
        
        # Run migrations
        result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully!")
            print(result.stdout)
        else:
            print("❌ Migration failed!")
            print(f"Error: {result.stderr}")
            print("Attempting to create tables directly...")
            
            # Try direct SQL as fallback
            try:
                import psycopg2
                from urllib.parse import urlparse
                
                db_url = os.environ.get("DATABASE_URL", "")
                if db_url.startswith("postgres://"):
                    db_url = db_url.replace("postgres://", "postgresql://", 1)
                
                parsed = urlparse(db_url)
                conn = psycopg2.connect(
                    host=parsed.hostname,
                    port=parsed.port,
                    database=parsed.path[1:],
                    user=parsed.username,
                    password=parsed.password
                )
                
                with conn.cursor() as cur:
                    # Read and execute SQL file
                    with open("create_outreach_tables.sql", "r") as f:
                        sql = f.read()
                    cur.execute(sql)
                    conn.commit()
                    print("✅ Tables created via direct SQL!")
                
                conn.close()
            except Exception as e:
                print(f"❌ Direct SQL also failed: {e}")
    
    except Exception as e:
        print(f"❌ Migration error: {e}")

async def ensure_tables_exist():
    """Ensure outreach tables exist by checking and creating if needed."""
    print("=" * 60)
    print("CHECKING DATABASE TABLES")
    print("=" * 60)
    
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        db_url = os.environ.get("DATABASE_URL", "")
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        
        parsed = urlparse(db_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
        
        with conn.cursor() as cur:
            # Check if outreach_messages table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'outreach_messages'
                );
            """)
            outreach_messages_exists = cur.fetchone()[0]
            
            # Check if outreach_templates table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'outreach_templates'
                );
            """)
            outreach_templates_exists = cur.fetchone()[0]
            
            print(f"outreach_messages table exists: {outreach_messages_exists}")
            print(f"outreach_templates table exists: {outreach_templates_exists}")
            
            # If tables don't exist, create them
            if not outreach_messages_exists or not outreach_templates_exists:
                print("Creating missing tables...")
                with open("create_outreach_tables.sql", "r") as f:
                    sql = f.read()
                cur.execute(sql)
                conn.commit()
                print("✅ Tables created successfully!")
            else:
                print("✅ All required tables already exist!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking/creating tables: {e}")
        return False

async def main():
    """Main startup function."""
    print("Starting Railway backend...")
    
    # Always run migrations on Railway
    run_migrations()
    
    # Ensure tables exist as a backup
    await ensure_tables_exist()
    
    # Start the server
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config("app.main:app", host="0.0.0.0", port=port, access_log=True)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())