#!/usr/bin/env python3
"""Run database migrations once on startup."""

import subprocess
import sys
import os

print("Running database migrations...")

try:
    # Run alembic upgrade
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        cwd="/app"  # Railway working directory
    )
    
    if result.returncode == 0:
        print("✅ Migrations completed successfully!")
        print(result.stdout)
    else:
        print("❌ Migration failed!")
        print(result.stderr)
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error running migrations: {e}")
    sys.exit(1)

print("Starting the application...")
# Continue with normal startup
os.system("uvicorn app.main:app --host 0.0.0.0 --port 8000")