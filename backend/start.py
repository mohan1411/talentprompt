import os
import sys
import asyncio
import uvicorn

async def main():
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