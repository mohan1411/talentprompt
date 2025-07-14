#!/usr/bin/env python3
"""Initialize database with tables and first superuser."""

import asyncio
import os
from sqlalchemy import text

from app.db.session import engine, async_session_maker
from app.db.base import Base
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.core.config import settings

async def init_db():
    """Initialize database."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Database tables created")
    
    # Create first superuser if it doesn't exist
    async with async_session_maker() as db:
        try:
            # Check if any users exist
            result = await db.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            if user_count == 0:
                # Create first superuser
                user_in = UserCreate(
                    email=settings.FIRST_SUPERUSER,
                    username=settings.FIRST_SUPERUSER.split('@')[0],
                    password=settings.FIRST_SUPERUSER_PASSWORD,
                    full_name="Admin User",
                    is_superuser=True,
                    is_active=True
                )
                await create_user(db, user_in)
                print(f"✓ Created first superuser: {settings.FIRST_SUPERUSER}")
            else:
                print(f"✓ Users already exist ({user_count} users)")
                
        except Exception as e:
            print(f"✗ Error creating first superuser: {e}")
            raise

if __name__ == "__main__":
    print("Initializing database...")
    asyncio.run(init_db())
    print("Database initialization complete!")