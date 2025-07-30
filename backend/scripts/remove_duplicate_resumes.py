#!/usr/bin/env python3
"""Script to remove duplicate resumes and keep only the most recent one per email."""

import asyncio
import logging
import sys
import os
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables if .env file exists
from dotenv import load_dotenv
load_dotenv()

from app.db.session import async_session_maker
from app.models.resume import Resume

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def remove_duplicate_resumes():
    """Find and remove duplicate resumes, keeping only the most recent one per email per recruiter."""
    async with async_session_maker() as db:
        try:
            # Find all duplicate email/user_id combinations
            duplicates_query = select(
                Resume.email,
                Resume.user_id,
                func.count(Resume.id).label('count')
            ).where(
                Resume.status == 'active'
            ).group_by(
                Resume.email, Resume.user_id
            ).having(
                func.count(Resume.id) > 1
            )
            
            result = await db.execute(duplicates_query)
            duplicates = result.all()
            
            logger.info(f"Found {len(duplicates)} email/recruiter combinations with duplicates")
            
            total_removed = 0
            
            for email, user_id, count in duplicates:
                logger.info(f"Processing duplicates for {email} (recruiter: {user_id}) - {count} copies found")
                
                # Get all resumes for this email/user combination, ordered by creation date
                resumes_query = select(Resume).where(
                    and_(
                        Resume.email == email,
                        Resume.user_id == user_id,
                        Resume.status == 'active'
                    )
                ).order_by(Resume.created_at.desc())
                
                result = await db.execute(resumes_query)
                resumes = result.scalars().all()
                
                # Keep the first (most recent) one, mark others as deleted
                for i, resume in enumerate(resumes):
                    if i == 0:
                        logger.info(f"  Keeping resume {resume.id} created at {resume.created_at}")
                    else:
                        logger.info(f"  Marking resume {resume.id} as deleted (created at {resume.created_at})")
                        resume.status = 'deleted'
                        total_removed += 1
            
            await db.commit()
            logger.info(f"Successfully removed {total_removed} duplicate resumes")
            
        except Exception as e:
            logger.error(f"Error removing duplicates: {e}")
            await db.rollback()
            raise


async def main():
    """Run the duplicate removal script."""
    logger.info("Starting duplicate resume removal...")
    await remove_duplicate_resumes()
    logger.info("Duplicate removal completed!")


if __name__ == "__main__":
    asyncio.run(main())