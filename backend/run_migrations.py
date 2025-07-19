#!/usr/bin/env python
"""Run database migrations."""

import asyncio
import sys
from alembic import command
from alembic.config import Config
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def run_migrations():
    """Run all pending migrations."""
    # Get the alembic.ini file path
    alembic_ini = backend_dir / "alembic.ini"
    
    # Create Alembic configuration
    alembic_cfg = Config(str(alembic_ini))
    
    # Run migrations
    try:
        print("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()