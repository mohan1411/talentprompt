#!/usr/bin/env python3
"""Fix Anil's skills to include WebSphere technologies."""

import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.resume import Resume

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_anil_skills():
    """Update Anil's skills to include WebSphere technologies."""
    
    # Create database connection
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as db:
        # Find Anil's profile
        stmt = select(Resume).where(
            Resume.first_name == "Anil",
            Resume.last_name == "Narasimhappa"
        )
        result = await db.execute(stmt)
        anil = result.scalar_one_or_none()
        
        if not anil:
            logger.error("Anil Narasimhappa not found in database!")
            return
        
        logger.info(f"Found Anil's profile: {anil.id}")
        logger.info(f"Current skills: {anil.skills}")
        
        # Update skills to include WebSphere technologies
        # Based on the Chrome extension data, Anil should have WebSphere skills
        new_skills = [
            "WebSphere",
            "WebSphere Application Server",
            "WebSphere Message Broker",
            "IBM MQ",
            "Java",
            "J2EE",
            "Enterprise Integration",
            "Middleware",
            "SOA",
            "Web Services"
        ]
        
        # Preserve any existing skills that aren't duplicates
        existing_skills = anil.skills or []
        for skill in existing_skills:
            if skill and skill not in new_skills:
                new_skills.append(skill)
        
        anil.skills = new_skills
        
        logger.info(f"Updated skills: {anil.skills}")
        
        await db.commit()
        logger.info("Successfully updated Anil's skills!")
        
        # Verify the update
        await db.refresh(anil)
        logger.info(f"Verified skills after commit: {anil.skills}")


if __name__ == "__main__":
    asyncio.run(fix_anil_skills())