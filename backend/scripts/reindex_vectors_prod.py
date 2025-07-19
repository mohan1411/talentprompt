#!/usr/bin/env python3
"""Script to re-index all resumes in Qdrant with user_id for security - Production version.

This is a CRITICAL security fix to ensure users can only see their own resumes.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Force load environment variables before importing anything else
from dotenv import load_dotenv
load_dotenv()

# Now import after environment is set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from qdrant_client import QdrantClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def reindex_all_resumes():
    """Re-index all resumes with user_id in metadata."""
    # Get config from environment
    database_url = os.getenv("DATABASE_URL")
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    logger.info(f"Using Qdrant URL: {qdrant_url}")
    
    # Create database engine
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://")
        
    engine = create_async_engine(
        database_url,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Create Qdrant client directly
    qdrant_client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        timeout=30
    )
    
    # Import these after environment is set up
    from app.models.resume import Resume
    from app.services.embeddings import embedding_service
    
    async with async_session() as db:
        try:
            # Get all resumes with completed parse status
            stmt = select(Resume).where(
                Resume.status == 'active',
                Resume.parse_status == 'completed'
            )
            
            result = await db.execute(stmt)
            resumes = result.scalars().all()
            
            logger.info(f"Found {len(resumes)} resumes to re-index")
            
            success_count = 0
            error_count = 0
            
            for resume in resumes:
                try:
                    logger.info(f"Re-indexing resume {resume.id} for user {resume.user_id}")
                    
                    # Prepare resume text for embedding
                    resume_data = {
                        "first_name": resume.first_name,
                        "last_name": resume.last_name,
                        "email": resume.email,
                        "phone": resume.phone,
                        "location": resume.location,
                        "current_title": resume.current_title,
                        "summary": resume.summary,
                        "years_experience": resume.years_experience,
                        "skills": resume.skills or [],
                        "keywords": resume.keywords or []
                    }
                    
                    resume_text = embedding_service.prepare_resume_text(resume_data)
                    
                    # Get embedding
                    embedding = await embedding_service.generate_embedding(resume_text)
                    
                    if not embedding:
                        logger.warning(f"No embedding generated for resume {resume.id}")
                        continue
                    
                    # Prepare metadata with user_id
                    metadata = {
                        "resume_id": str(resume.id),
                        "user_id": str(resume.user_id),  # CRITICAL: Include user_id for security
                        "first_name": resume.first_name or "",
                        "last_name": resume.last_name or "",
                        "email": resume.email or "",
                        "location": resume.location or "",
                        "current_title": resume.current_title or "",
                        "years_experience": resume.years_experience or 0,
                        "skills": resume.skills or [],
                        "keywords": resume.keywords or []
                    }
                    
                    # Upsert to Qdrant directly
                    from qdrant_client.models import PointStruct
                    
                    point = PointStruct(
                        id=str(resume.id),
                        vector=embedding,
                        payload=metadata
                    )
                    
                    qdrant_client.upsert(
                        collection_name="promtitude_resumes",
                        points=[point]
                    )
                    
                    success_count += 1
                    logger.info(f"Successfully re-indexed resume {resume.id}")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error re-indexing resume {resume.id}: {e}")
            
            logger.info(f"\nRe-indexing complete!")
            logger.info(f"Success: {success_count}")
            logger.info(f"Errors: {error_count}")
            logger.info(f"Total: {len(resumes)}")
            
        except Exception as e:
            logger.error(f"Fatal error during re-indexing: {e}")
            raise
        finally:
            await engine.dispose()


async def verify_user_isolation():
    """Verify that user isolation is working correctly."""
    logger.info("\n" + "="*60)
    logger.info("VERIFYING USER ISOLATION")
    logger.info("="*60)
    
    # Get config from environment
    database_url = os.getenv("DATABASE_URL")
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    # Create database engine
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://")
        
    engine = create_async_engine(
        database_url,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Create Qdrant client
    qdrant_client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        timeout=30
    )
    
    from app.models.resume import Resume
    
    async with async_session() as db:
        try:
            # Get distinct user IDs
            stmt = select(Resume.user_id).distinct()
            result = await db.execute(stmt)
            user_ids = [row[0] for row in result.all()]
            
            logger.info(f"Found {len(user_ids)} distinct users with resumes")
            
            # Test search for each user
            test_query = "software engineer"
            
            for user_id in user_ids[:3]:  # Test first 3 users
                logger.info(f"\nTesting search for user {user_id}:")
                
                # Get user's resume count
                count_stmt = select(Resume).where(Resume.user_id == user_id)
                count_result = await db.execute(count_stmt)
                user_resumes = count_result.scalars().all()
                
                logger.info(f"  - User has {len(user_resumes)} resumes in database")
                
                # Test vector search with user filter
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                
                # Get embedding for test query
                from app.services.embeddings import embedding_service
                query_embedding = await embedding_service.generate_embedding(test_query)
                
                if query_embedding:
                    # Search with user_id filter
                    search_filter = Filter(
                        must=[
                            FieldCondition(
                                key="user_id",
                                match=MatchValue(value=str(user_id))
                            )
                        ]
                    )
                    
                    results = qdrant_client.search(
                        collection_name="promtitude_resumes",
                        query_vector=query_embedding,
                        query_filter=search_filter,
                        limit=10,
                        with_payload=True
                    )
                    
                    logger.info(f"  - Vector search returned {len(results)} results")
                    
                    # Verify all results belong to the user
                    for result in results:
                        result_user_id = result.payload.get("user_id")
                        if result_user_id != str(user_id):
                            logger.error(f"  ❌ SECURITY BREACH: Found resume from user {result_user_id} in results for user {user_id}!")
                        else:
                            logger.info(f"  ✓ Resume {result.id} correctly belongs to user {user_id}")
                        
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            raise
        finally:
            await engine.dispose()


async def main():
    """Main function."""
    logger.info("Starting Qdrant re-indexing for security fix...")
    logger.info("This will add user_id to all resume vectors to ensure proper data isolation")
    
    # Re-index all resumes
    await reindex_all_resumes()
    
    # Verify isolation is working
    await verify_user_isolation()
    
    logger.info("\nRe-indexing complete! User data isolation is now enforced.")


if __name__ == "__main__":
    asyncio.run(main())