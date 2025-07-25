"""Debug script to test the duplicate check logic"""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from app.models.resume import Resume

# Your user ID
USER_ID = "d48c0d47-d6d3-404b-9f58-8552534f9b4d"

# Test URLs
TEST_URLS = [
    "https://www.linkedin.com/in/yeshaswini-k-p-0252b2131",
    "https://www.linkedin.com/in/atul-singh-1a7421104"
]

async def test_duplicate_check():
    # Create database connection
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        for url in TEST_URLS:
            print(f"\nTesting URL: {url}")
            
            # Exact duplicate check from the backend
            existing_query = select(Resume).where(
                Resume.linkedin_url == url,
                Resume.user_id == USER_ID,
                Resume.status != 'deleted'
            )
            result = await db.execute(existing_query)
            existing_resume = result.scalar_one_or_none()
            
            print(f"Found for your user (excluding deleted): {existing_resume is not None}")
            if existing_resume:
                print(f"  - ID: {existing_resume.id}")
                print(f"  - Status: {existing_resume.status}")
            
            # Check ALL resumes for this URL (any user)
            all_query = select(Resume).where(
                Resume.linkedin_url == url
            )
            all_result = await db.execute(all_query)
            all_resumes = all_result.scalars().all()
            
            print(f"Found globally (all users): {len(all_resumes)}")
            for r in all_resumes:
                print(f"  - User: {r.user_id}, Status: {r.status}")
            
            # Check with trailing slash
            all_query_slash = select(Resume).where(
                Resume.linkedin_url == url + "/"
            )
            slash_result = await db.execute(all_query_slash)
            slash_resumes = slash_result.scalars().all()
            
            print(f"Found with trailing slash: {len(slash_resumes)}")
            for r in slash_resumes:
                print(f"  - User: {r.user_id}, Status: {r.status}")

if __name__ == "__main__":
    asyncio.run(test_duplicate_check())