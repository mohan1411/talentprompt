#!/usr/bin/env python3
"""Diagnostic script to check vector search issues for admin@promtitude.com."""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.models.resume import Resume
from app.models.user import User
from app.services.vector_search import vector_search
from app.services.embeddings import embedding_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def diagnose_vector_search():
    """Diagnose vector search issues for admin@promtitude.com."""
    
    # Create database engine
    engine = create_async_engine(
        settings.DATABASE_URL,
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
    
    async with async_session() as db:
        try:
            logger.info("\n" + "="*80)
            logger.info("VECTOR SEARCH DIAGNOSTIC for test@example.com")
            logger.info("="*80 + "\n")
            
            # 1. Find the user with most resumes (test@example.com)
            stmt = select(User).where(User.email == "test@example.com")
            result = await db.execute(stmt)
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                logger.error("❌ User test@example.com not found!")
                return
            
            logger.info(f"✓ Found user test@example.com: ID={admin_user.id}")
            
            # 2. Count resumes in PostgreSQL
            count_stmt = select(func.count(Resume.id)).where(
                Resume.user_id == admin_user.id,
                Resume.status == 'active',
                Resume.parse_status == 'completed'
            )
            count_result = await db.execute(count_stmt)
            pg_count = count_result.scalar() or 0
            
            logger.info(f"\n📊 PostgreSQL Statistics:")
            logger.info(f"   - Active & parsed resumes: {pg_count}")
            
            # Get more details about resume status
            status_stmt = select(
                Resume.status,
                Resume.parse_status,
                func.count(Resume.id)
            ).where(
                Resume.user_id == admin_user.id
            ).group_by(Resume.status, Resume.parse_status)
            
            status_result = await db.execute(status_stmt)
            status_counts = status_result.all()
            
            logger.info(f"   - Resume status breakdown:")
            for status, parse_status, count in status_counts:
                logger.info(f"     * {status}/{parse_status}: {count}")
            
            # 3. Check Qdrant connection and collection
            logger.info(f"\n🔌 Qdrant Connection Check:")
            try:
                collection_info = await vector_search.get_collection_info()
                logger.info(f"   - Status: {collection_info.get('status', 'unknown')}")
                logger.info(f"   - Collection: {collection_info.get('collection', 'unknown')}")
                logger.info(f"   - Total points: {collection_info.get('points_count', 0)}")
                
                if collection_info.get('status') == 'error':
                    logger.error(f"   - Error: {collection_info.get('error')}")
            except Exception as e:
                logger.error(f"   - Failed to connect to Qdrant: {e}")
            
            # 4. Search for admin's resumes in Qdrant
            logger.info(f"\n🔍 Searching for admin's resumes in Qdrant:")
            try:
                # Try a simple search
                test_results = await vector_search.search_similar(
                    query="software engineer developer",
                    user_id=str(admin_user.id),
                    limit=10
                )
                
                logger.info(f"   - Vector search returned: {len(test_results)} results")
                
                if test_results:
                    logger.info("   - Sample results:")
                    for i, result in enumerate(test_results[:3]):
                        metadata = result.get("metadata", {})
                        logger.info(f"     {i+1}. {metadata.get('first_name', 'Unknown')} {metadata.get('last_name', '')}")
                        logger.info(f"        Score: {result.get('score', 0):.4f}")
                        logger.info(f"        User ID: {metadata.get('user_id', 'missing')}")
            except Exception as e:
                logger.error(f"   - Vector search failed: {e}")
            
            # 5. Test embedding generation
            logger.info(f"\n🧪 Testing embedding generation:")
            try:
                test_text = "Senior Python Developer with 10 years of experience in Django and FastAPI"
                embedding = await embedding_service.generate_embedding(test_text)
                
                if embedding:
                    logger.info(f"   ✓ Embedding generated successfully")
                    logger.info(f"   - Dimension: {len(embedding)}")
                    logger.info(f"   - Sample values: {embedding[:5]}...")
                else:
                    logger.error("   ❌ Failed to generate embedding")
            except Exception as e:
                logger.error(f"   ❌ Embedding generation error: {e}")
            
            # 6. Sample a few resumes to check if they're indexed
            logger.info(f"\n📋 Checking individual resumes:")
            sample_stmt = select(Resume).where(
                Resume.user_id == admin_user.id,
                Resume.status == 'active',
                Resume.parse_status == 'completed'
            ).limit(5)
            
            sample_result = await db.execute(sample_stmt)
            sample_resumes = sample_result.scalars().all()
            
            for resume in sample_resumes:
                logger.info(f"\n   Resume: {resume.first_name} {resume.last_name} (ID: {resume.id})")
                
                # Try to search for this specific resume
                search_query = f"{resume.first_name} {resume.last_name}"
                if resume.current_title:
                    search_query += f" {resume.current_title}"
                
                specific_results = await vector_search.search_similar(
                    query=search_query,
                    user_id=str(admin_user.id),
                    limit=5
                )
                
                found = any(r["resume_id"] == str(resume.id) for r in specific_results)
                if found:
                    logger.info(f"   ✓ Found in vector search")
                else:
                    logger.info(f"   ❌ NOT found in vector search")
            
            # 7. Configuration check
            logger.info(f"\n⚙️  Configuration Check:")
            logger.info(f"   - QDRANT_URL: {settings.QDRANT_URL}")
            logger.info(f"   - QDRANT_COLLECTION: {settings.QDRANT_COLLECTION_NAME}")
            logger.info(f"   - OPENAI_API_KEY: {'✓ Set' if settings.OPENAI_API_KEY else '❌ Missing'}")
            logger.info(f"   - EMBEDDING_MODEL: {settings.EMBEDDING_MODEL}")
            
            # 8. Summary and recommendations
            logger.info(f"\n" + "="*80)
            logger.info("DIAGNOSTIC SUMMARY")
            logger.info("="*80)
            
            issues = []
            
            if pg_count == 0:
                issues.append("No active/parsed resumes found in PostgreSQL")
            
            if collection_info.get('status') == 'error':
                issues.append("Cannot connect to Qdrant")
            elif collection_info.get('points_count', 0) == 0:
                issues.append("Qdrant collection is empty")
            
            if not settings.OPENAI_API_KEY:
                issues.append("OpenAI API key is missing")
            
            if test_results is not None and len(test_results) == 0:
                issues.append("Vector search returns no results")
            
            if issues:
                logger.info("\n🚨 Issues found:")
                for issue in issues:
                    logger.info(f"   - {issue}")
                
                logger.info("\n💡 Recommended actions:")
                if "Qdrant collection is empty" in issues or "Vector search returns no results" in issues:
                    logger.info("   1. Run the reindexing script: python scripts/reindex_vectors.py")
                if "Cannot connect to Qdrant" in issues:
                    logger.info("   1. Check if Qdrant is running: docker ps | grep qdrant")
                    logger.info("   2. Verify QDRANT_URL in .env file")
                if "OpenAI API key is missing" in issues:
                    logger.info("   1. Set OPENAI_API_KEY in .env file")
            else:
                logger.info("\n✅ No obvious issues found. Vector search should be working.")
                logger.info("   Consider running reindexing script if search results are still incorrect.")
            
        except Exception as e:
            logger.error(f"Fatal error during diagnosis: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(diagnose_vector_search())