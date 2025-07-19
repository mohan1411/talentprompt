import os
import sys
import asyncio
import uvicorn

async def main():
    # Run debug script if requested
    if "--debug" in sys.argv or os.environ.get("DEBUG_ENV", "false").lower() == "true":
        import subprocess
        subprocess.run([sys.executable, "debug_env.py"])
        print("\n" + "="*50 + "\n")
    
    # Run database migrations
    if "--skip-migrations" not in sys.argv and os.environ.get("SKIP_MIGRATIONS", "false").lower() != "true":
        print("Running database migrations...")
        try:
            import subprocess
            result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Migrations completed successfully!")
            else:
                print(f"⚠️ Migration warning: {result.stderr}")
        except Exception as e:
            print(f"⚠️ Could not run migrations: {str(e)}")
    
    # Check if we should initialize the database
    if "--init-db" in sys.argv or os.environ.get("INIT_DB", "false").lower() == "true":
        print("Initializing database...")
        from init_db import init_db
        await init_db()
    
    # Start the server
    port = int(os.environ.get("PORT", 8000))
    config = uvicorn.Config("app.main:app", host="0.0.0.0", port=port, access_log=True)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())