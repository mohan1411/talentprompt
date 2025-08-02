#!/usr/bin/env python3
"""
Run the app without database for testing security features
"""

import os

# Set environment variable to skip DB
os.environ['SKIP_DB_INIT'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./dummy.db'

# Import and run the app
import uvicorn
from app.main import app

if __name__ == "__main__":
    print("Starting server without database initialization...")
    print("This is only for testing security features!")
    uvicorn.run(app, host="0.0.0.0", port=8000)