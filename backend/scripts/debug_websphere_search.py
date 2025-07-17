#!/usr/bin/env python3
"""Debug script to diagnose WebSphere search issues."""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select, func, text, String
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.resume import Resume

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def debug_websphere_search():
    """Debug WebSphere search issues."""
    # Create database connection
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        logger.info("=== WebSphere Search Debug ===\n")
        
        # 1. Check total resumes
        total_stmt = select(func.count(Resume.id))
        total_result = await db.execute(total_stmt)
        total_count = total_result.scalar()
        logger.info(f"Total resumes in database: {total_count}")
        
        # 2. Check resumes with skills
        skills_stmt = select(func.count(Resume.id)).where(Resume.skills.isnot(None))
        skills_result = await db.execute(skills_stmt)
        skills_count = skills_result.scalar()
        logger.info(f"Resumes with skills data: {skills_count}")
        
        # 3. Find all variations of WebSphere in skills
        logger.info("\n--- Searching for WebSphere variations in skills ---")
        websphere_variations = [
            'WebSphere', 'websphere', 'WEBSPHERE', 'Websphere',
            'web sphere', 'Web Sphere', 'WEB SPHERE'
        ]
        
        for variation in websphere_variations:
            # Search in skills JSON
            stmt = select(
                Resume.id,
                Resume.first_name,
                Resume.last_name,
                Resume.skills
            ).where(
                func.cast(Resume.skills, String).ilike(f'%{variation}%')
            ).limit(5)
            
            result = await db.execute(stmt)
            rows = result.all()
            
            if rows:
                logger.info(f"\nFound {len(rows)} resumes with '{variation}' in skills:")
                for row in rows:
                    logger.info(f"  - {row.first_name} {row.last_name} (ID: {row.id})")
                    if row.skills:
                        # Find the actual skill entry
                        matching_skills = [s for s in row.skills if variation.lower() in s.lower()]
                        logger.info(f"    Matching skills: {matching_skills}")
        
        # 4. Search in raw_text
        logger.info("\n--- Searching for WebSphere in raw_text ---")
        raw_text_stmt = select(func.count(Resume.id)).where(
            Resume.raw_text.ilike('%websphere%')
        )
        raw_text_result = await db.execute(raw_text_stmt)
        raw_text_count = raw_text_result.scalar()
        logger.info(f"Resumes with 'websphere' in raw_text: {raw_text_count}")
        
        # 5. Get samples of resumes with WebSphere in raw_text but not in skills
        logger.info("\n--- Resumes with WebSphere in text but not in skills ---")
        missing_skills_stmt = select(
            Resume.id,
            Resume.first_name,
            Resume.last_name,
            Resume.skills,
            Resume.raw_text
        ).where(
            Resume.raw_text.ilike('%websphere%'),
            ~func.cast(Resume.skills, String).ilike('%websphere%')
        ).limit(3)
        
        missing_result = await db.execute(missing_skills_stmt)
        missing_rows = missing_result.all()
        
        if missing_rows:
            logger.info(f"Found {len(missing_rows)} resumes with WebSphere in text but not in skills:")
            for row in missing_rows:
                logger.info(f"\n  - {row.first_name} {row.last_name} (ID: {row.id})")
                logger.info(f"    Current skills: {row.skills[:5] if row.skills else 'None'}...")
                
                # Extract WebSphere context from raw_text
                if row.raw_text:
                    text_lower = row.raw_text.lower()
                    websphere_index = text_lower.find('websphere')
                    if websphere_index != -1:
                        start = max(0, websphere_index - 50)
                        end = min(len(row.raw_text), websphere_index + 100)
                        context = row.raw_text[start:end]
                        logger.info(f"    WebSphere context: '...{context}...'")
        
        # 6. Test the search query directly
        logger.info("\n--- Testing direct SQL queries ---")
        
        # Test JSONB array search
        jsonb_query = """
        SELECT COUNT(*) FROM resumes 
        WHERE EXISTS (
            SELECT 1 FROM jsonb_array_elements_text(skills::jsonb) AS skill
            WHERE skill ILIKE '%websphere%'
        )
        """
        result = await db.execute(text(jsonb_query))
        jsonb_count = result.scalar()
        logger.info(f"JSONB array search for 'websphere': {jsonb_count} results")
        
        # Test cast to string search
        cast_query = """
        SELECT COUNT(*) FROM resumes 
        WHERE CAST(skills AS TEXT) ILIKE '%websphere%'
        """
        result = await db.execute(text(cast_query))
        cast_count = result.scalar()
        logger.info(f"Cast to string search for 'websphere': {cast_count} results")
        
        logger.info("\n=== Debug Complete ===")


async def fix_websphere_skills():
    """Fix WebSphere skills that might be missing from the skills array."""
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        logger.info("\n=== Fixing WebSphere Skills ===")
        
        # Find resumes with WebSphere in raw_text but not in skills
        stmt = select(Resume).where(
            Resume.raw_text.ilike('%websphere%'),
            Resume.status == 'active'
        )
        
        result = await db.execute(stmt)
        resumes = result.scalars().all()
        
        fixed_count = 0
        for resume in resumes:
            if not resume.skills:
                resume.skills = []
            
            # Check if WebSphere is already in skills (case-insensitive)
            has_websphere = any('websphere' in skill.lower() for skill in resume.skills)
            
            if not has_websphere:
                # Extract WebSphere variations from text
                text_lower = resume.raw_text.lower()
                websphere_skills = set()
                
                # Common WebSphere products
                websphere_products = {
                    'websphere application server': 'WebSphere Application Server',
                    'websphere mq': 'WebSphere MQ',
                    'websphere message broker': 'WebSphere Message Broker',
                    'websphere portal': 'WebSphere Portal',
                    'websphere commerce': 'WebSphere Commerce',
                    'websphere': 'WebSphere'  # Generic
                }
                
                for product_lower, product_proper in websphere_products.items():
                    if product_lower in text_lower:
                        websphere_skills.add(product_proper)
                
                if websphere_skills:
                    # Add WebSphere skills
                    resume.skills.extend(list(websphere_skills))
                    # Remove duplicates while preserving order
                    resume.skills = list(dict.fromkeys(resume.skills))
                    
                    logger.info(f"Fixed {resume.first_name} {resume.last_name}: Added {websphere_skills}")
                    fixed_count += 1
        
        if fixed_count > 0:
            await db.commit()
            logger.info(f"\nFixed {fixed_count} resumes with missing WebSphere skills")
        else:
            logger.info("\nNo resumes needed fixing")


async def main():
    """Run debug diagnostics."""
    await debug_websphere_search()
    
    # Optionally fix the issues
    response = input("\nDo you want to fix missing WebSphere skills? (y/n): ")
    if response.lower() == 'y':
        await fix_websphere_skills()


if __name__ == "__main__":
    asyncio.run(main())