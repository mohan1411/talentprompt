#!/usr/bin/env python
"""Run migrations on Railway."""
import os
import sys
import subprocess

print("Running database migrations on Railway...")

# Run alembic migrations
result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Migrations completed successfully!")
    print(result.stdout)
else:
    print("❌ Migration failed!")
    print(result.stderr)
    sys.exit(1)