#!/usr/bin/env python3
"""Script to investigate search behavior for product manager queries."""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database configuration
DB_URL = os.getenv("DATABASE_URL", "postgresql://talentprompt:talentprompt@localhost:5433/talentprompt")
# Convert to async URL if needed
if DB_URL.startswith("postgresql://"):
    ASYNC_DB_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DB_URL = DB_URL


async def investigate_database():
    """Investigate database content and search behavior."""
    
    # Create async engine
    engine = create_async_engine(ASYNC_DB_URL, echo=True)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        print("\n=== INVESTIGATING DATABASE ===\n")
        
        # 1. Check total number of resumes
        result = await session.execute(
            text("SELECT COUNT(*) FROM resumes WHERE status = 'active'")
        )
        total_count = result.scalar()
        print(f"Total active resumes: {total_count}")
        
        # 2. Check unique job positions
        print("\n--- Job Positions in Database ---")
        result = await session.execute(
            text("""
                SELECT DISTINCT job_position, COUNT(*) as count 
                FROM resumes 
                WHERE job_position IS NOT NULL 
                GROUP BY job_position 
                ORDER BY count DESC
            """)
        )
        positions = result.fetchall()
        for pos, count in positions:
            print(f"  {pos}: {count} resumes")
        
        # 3. Check unique current titles
        print("\n--- Current Titles in Database ---")
        result = await session.execute(
            text("""
                SELECT DISTINCT current_title, COUNT(*) as count 
                FROM resumes 
                WHERE current_title IS NOT NULL 
                GROUP BY current_title 
                ORDER BY count DESC
            """)
        )
        titles = result.fetchall()
        for title, count in titles:
            print(f"  {title}: {count} resumes")
        
        # 4. Check resumes with "Product Manager" in current_title
        print("\n--- Resumes with 'Product Manager' in current_title ---")
        result = await session.execute(
            text("""
                SELECT id, first_name, last_name, current_title, job_position
                FROM resumes 
                WHERE current_title ILIKE '%product manager%'
                ORDER BY first_name, last_name
            """)
        )
        pm_resumes = result.fetchall()
        for resume in pm_resumes:
            print(f"  {resume.first_name} {resume.last_name}: {resume.current_title} (job_position: {resume.job_position})")
        
        # 5. Check if embeddings exist
        print("\n--- Embedding Status ---")
        result = await session.execute(
            text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(embedding) as with_embedding,
                    COUNT(*) - COUNT(embedding) as without_embedding
                FROM resumes 
                WHERE status = 'active'
            """)
        )
        emb_status = result.fetchone()
        print(f"  Total: {emb_status.total}")
        print(f"  With embeddings: {emb_status.with_embedding}")
        print(f"  Without embeddings: {emb_status.without_embedding}")
        
        # 6. Sample resume content for a Product Manager
        if pm_resumes:
            print("\n--- Sample Product Manager Resume Content ---")
            result = await session.execute(
                text("""
                    SELECT first_name, last_name, summary, skills
                    FROM resumes 
                    WHERE current_title ILIKE '%product manager%'
                    LIMIT 1
                """)
            )
            sample = result.fetchone()
            if sample:
                print(f"  Name: {sample.first_name} {sample.last_name}")
                print(f"  Summary: {sample.summary[:200]}..." if sample.summary else "  Summary: None")
                print(f"  Skills: {json.dumps(sample.skills) if sample.skills else 'None'}")
        
        # 7. Check what's actually being searched
        print("\n--- Testing Vector Search (if embeddings exist) ---")
        result = await session.execute(
            text("SELECT COUNT(*) FROM resumes WHERE embedding IS NOT NULL")
        )
        embedding_count = result.scalar()
        
        if embedding_count > 0:
            print(f"  Found {embedding_count} resumes with embeddings")
            
            # Get a sample embedding to understand the search
            result = await session.execute(
                text("""
                    SELECT 
                        r.id,
                        r.first_name,
                        r.last_name,
                        r.current_title,
                        r.summary
                    FROM resumes r
                    WHERE r.embedding IS NOT NULL
                    AND r.current_title ILIKE '%product manager%'
                    LIMIT 1
                """)
            )
            pm_with_embedding = result.fetchone()
            
            if pm_with_embedding:
                print(f"\n  Product Manager with embedding:")
                print(f"    {pm_with_embedding.first_name} {pm_with_embedding.last_name}")
                print(f"    Title: {pm_with_embedding.current_title}")
                print(f"    Summary preview: {pm_with_embedding.summary[:100]}..." if pm_with_embedding.summary else "    Summary: None")
        else:
            print("  No embeddings found in database - vector search won't work!")
    
    await engine.dispose()


async def main():
    """Main function."""
    try:
        await investigate_database()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure the database is running and accessible.")
        print("You may need to run: docker-compose up postgres")


if __name__ == "__main__":
    asyncio.run(main())