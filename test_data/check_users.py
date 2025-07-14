#!/usr/bin/env python3
"""Check users in database."""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database configuration
DB_URL = os.getenv("DATABASE_URL", "postgresql://talentprompt:talentprompt@localhost:5433/talentprompt")
# Convert to async URL if needed
if DB_URL.startswith("postgresql://"):
    ASYNC_DB_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DB_URL = DB_URL


async def check_users():
    """Check users in database."""
    
    # Create async engine
    engine = create_async_engine(ASYNC_DB_URL, echo=False)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        print("\n=== CHECKING USERS ===\n")
        
        # Check users
        result = await session.execute(
            text("SELECT id, email, full_name, is_active FROM users")
        )
        users = result.fetchall()
        
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  {user.email} - {user.full_name} (active: {user.is_active})")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_users())