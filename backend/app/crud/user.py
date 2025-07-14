"""User CRUD operations."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for users."""
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """Get user by username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """Create new user."""
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            full_name=obj_in.full_name,
            hashed_password=get_password_hash(obj_in.password),
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
            company=obj_in.company,
            job_title=obj_in.job_title,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, db: AsyncSession, *, db_obj: User, obj_in: UserUpdate
    ) -> User:
        """Update user."""
        update_data = obj_in.dict(exclude_unset=True)
        
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        return await super().update(db, db_obj=db_obj, obj_in=update_data)
    
    async def authenticate(
        self, db: AsyncSession, *, username: str, password: str
    ) -> Optional[User]:
        """Authenticate user by username/email and password."""
        # Try to get user by email first
        user = await self.get_by_email(db, email=username)
        if not user:
            # If not found, try username
            user = await self.get_by_username(db, username=username)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user


user = CRUDUser(User)


# Legacy function exports for backward compatibility
async def get_user(db: AsyncSession, user_id: str) -> Optional[User]:
    """Get user by ID."""
    return await user.get(db, id=user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    return await user.get_by_email(db, email=email)


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username."""
    return await user.get_by_username(db, username=username)


async def create_user(db: AsyncSession, user_create: UserCreate) -> User:
    """Create new user."""
    return await user.create(db, obj_in=user_create)


async def update_user(
    db: AsyncSession, db_user: User, user_update: UserUpdate
) -> User:
    """Update user."""
    return await user.update(db, db_obj=db_user, obj_in=user_update)


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    """Authenticate user by username/email and password."""
    return await user.authenticate(db, username=username, password=password)