#!/usr/bin/env python3
"""Create a test user for development."""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_maker
from app.crud.user import user as crud_user
from app.schemas.user import UserCreate
from app.core.config import settings

async def create_test_user():
    """Create a test user."""
    async with async_session_maker() as db: 
        # Create test user
        test_user = UserCreate(
            email="test@example.com",
            password="password123",
            full_name="Test User",
            username="testuser"
        )
        
        # Check if user already exists
        existing_user = await crud_user.get_by_email(db, email=test_user.email)
        if existing_user:
            print(f"User {test_user.email} already exists")
            return existing_user
            
        # Create new user
        user = await crud_user.create(db, obj_in=test_user)
        await db.commit()
        
        print(f"Created user: {user.email}")
        print(f"Password: password123")
        return user

if __name__ == "__main__":
    asyncio.run(create_test_user())