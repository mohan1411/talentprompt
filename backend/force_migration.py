#!/usr/bin/env python3
"""Force run the migration."""

import os
import sys
import subprocess
import time

# Wait for database to be ready
print("⏳ Waiting for database to be ready...")
time.sleep(5)

# First, try to run the migration
print("🔄 Running database migrations...")
try:
    # Change to app directory first
    os.chdir("/app")
    
    # Run alembic current to check status
    print("Checking current migration status...")
    subprocess.run(["alembic", "current"], check=False)
    
    # Run the migration
    print("Running alembic upgrade head...")
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
    
    print("Migration output:")
    print(result.stdout)
    if result.stderr:
        print("Migration errors:")
        print(result.stderr)
        
    if result.returncode == 0:
        print("✅ Migration completed successfully!")
    else:
        print("⚠️  Migration returned non-zero exit code, but continuing...")
        
except Exception as e:
    print(f"⚠️  Migration error: {e}")
    print("Continuing anyway...")

# Always start the app
print("🚀 Starting application...")
os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])