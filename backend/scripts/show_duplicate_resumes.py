#!/usr/bin/env python3
"""Script to show duplicate resumes without deleting them."""

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


async def show_duplicate_resumes():
    """Find and display duplicate resumes."""
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
            
            print(f"\n{'='*80}")
            print(f"Found {len(duplicates)} email/recruiter combinations with duplicates")
            print(f"{'='*80}\n")
            
            total_duplicates = 0
            
            for email, user_id, count in duplicates:
                print(f"\nEmail: {email}")
                print(f"Recruiter ID: {user_id}")
                print(f"Number of duplicates: {count}")
                print("-" * 40)
                
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
                
                for i, resume in enumerate(resumes):
                    status = "KEEP (most recent)" if i == 0 else "WOULD DELETE"
                    print(f"  [{status}] ID: {resume.id}")
                    print(f"    Name: {resume.first_name} {resume.last_name}")
                    print(f"    Created: {resume.created_at}")
                    print(f"    Updated: {resume.updated_at}")
                    if i > 0:
                        total_duplicates += 1
            
            print(f"\n{'='*80}")
            print(f"Total resumes that would be deleted: {total_duplicates}")
            print(f"{'='*80}\n")
            
        except Exception as e:
            logger.error(f"Error showing duplicates: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Run the duplicate display script."""
    print("Analyzing duplicate resumes...")
    await show_duplicate_resumes()
    print("\nAnalysis complete!")
    print("Run 'python scripts/remove_duplicate_resumes.py' to actually remove duplicates.")


if __name__ == "__main__":
    asyncio.run(main())