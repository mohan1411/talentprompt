"""Database session configuration."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    str(settings.DATABASE_URL),  # Convert to string
    echo=False,
    future=True,
    pool_size=40,  # Increased pool size
    max_overflow=10,  # Allow overflow connections
    pool_pre_ping=False,  # Disabled - causes issues with async
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create async session maker
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)