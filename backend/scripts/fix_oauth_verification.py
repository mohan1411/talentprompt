#!/usr/bin/env python3
"""Fix OAuth users verification status.

OAuth users should always be marked as verified since they've been
verified by their OAuth provider (Google/LinkedIn).
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_oauth_users_verification():
    """Update all OAuth users to be verified."""
    async with async_session_maker() as db:
        try:
            # Update all users with oauth_provider to be verified
            result = await db.execute(
                update(User)
                .where(User.oauth_provider.isnot(None))
                .where(User.is_verified == False)
                .values(is_verified=True)
            )
            
            updated_count = result.rowcount
            await db.commit()
            
            logger.info(f"Updated {updated_count} OAuth users to verified status")
            
            # Log details of updated users
            if updated_count > 0:
                from sqlalchemy import select
                oauth_users = await db.execute(
                    select(User)
                    .where(User.oauth_provider.isnot(None))
                    .where(User.is_verified == True)
                )
                users = oauth_users.scalars().all()
                for user in users:
                    logger.info(f"  - {user.email} ({user.oauth_provider})")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating OAuth users: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(fix_oauth_users_verification())