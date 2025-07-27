#!/usr/bin/env python3
"""Reindex all resumes into Qdrant vector database."""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from app.core.config import settings
from app.models.resume import Resume
from app.services.vector_search import vector_search


async def reindex_all_resumes(db: AsyncSession):
    """Reindex all resumes into Qdrant."""
    print("Starting resume reindexing...")
    
    # Get total count
    total_result = await db.execute(select(func.count(Resume.id)))
    total_count = total_result.scalar()
    print(f"Found {total_count} resumes to index")
    
    if total_count == 0:
        print("No resumes found in database!")
        return
    
    # Process in batches
    batch_size = 50
    indexed_count = 0
    error_count = 0
    
    for offset in range(0, total_count, batch_size):
        print(f"\nProcessing batch {offset//batch_size + 1} ({offset}-{min(offset + batch_size, total_count)} of {total_count})")
        
        # Get batch of resumes
        stmt = select(Resume).offset(offset).limit(batch_size)
        result = await db.execute(stmt)
        resumes = result.scalars().all()
        
        for resume in resumes:
            try:
                # Create searchable text
                searchable_text = f"{resume.first_name} {resume.last_name} "
                if resume.current_title:
                    searchable_text += f"{resume.current_title} "
                if resume.summary:
                    searchable_text += f"{resume.summary} "
                if resume.skills:
                    searchable_text += " ".join(resume.skills)
                
                # Create metadata
                metadata = {
                    "user_id": str(resume.user_id),  # CRITICAL: Must include user_id
                    "first_name": resume.first_name,
                    "last_name": resume.last_name,
                    "email": resume.email,
                    "current_title": resume.current_title,
                    "location": resume.location,
                    "years_experience": resume.years_experience,
                    "skills": resume.skills or [],
                    "created_at": resume.created_at.isoformat() if resume.created_at else None
                }
                
                # Index in Qdrant
                embedding = await vector_search.index_resume(
                    resume_id=str(resume.id),
                    text=searchable_text,
                    metadata=metadata
                )
                
                if embedding:
                    indexed_count += 1
                    print(f"  ✓ Indexed: {resume.first_name} {resume.last_name} (ID: {resume.id})")
                else:
                    error_count += 1
                    print(f"  ✗ Failed: {resume.first_name} {resume.last_name} (ID: {resume.id})")
                    
            except Exception as e:
                error_count += 1
                print(f"  ✗ Error indexing resume {resume.id}: {e}")
        
        # Small delay between batches
        await asyncio.sleep(0.5)
    
    print("\n" + "="*60)
    print("REINDEXING COMPLETE")
    print("="*60)
    print(f"Total resumes: {total_count}")
    print(f"Successfully indexed: {indexed_count}")
    print(f"Errors: {error_count}")
    
    if indexed_count > 0:
        print("\n✅ Resumes are now searchable with vector search!")
    else:
        print("\n❌ No resumes were indexed. Check error messages above.")


async def verify_indexing():
    """Verify that indexing worked."""
    print("\n" + "="*60)
    print("VERIFYING INDEXING")
    print("="*60)
    
    try:
        # Check collection info
        info = await vector_search.get_collection_info()
        print(f"Collection status: {info.get('status', 'unknown')}")
        print(f"Points in collection: {info.get('points_count', 0)}")
        
        # Try a test search
        print("\nTesting search functionality...")
        results = await vector_search.search_similar(
            query="python developer",
            user_id=None,  # Search across all users for test
            limit=3
        )
        
        print(f"Test search returned {len(results)} results")
        if results:
            print("\nTop result:")
            print(f"  - Score: {results[0]['score']:.3f}")
            print(f"  - User ID: {results[0]['metadata'].get('user_id', 'N/A')}")
            
    except Exception as e:
        print(f"Error during verification: {e}")


async def main():
    """Run the reindexing process."""
    print("="*60)
    print("QDRANT RESUME REINDEXING")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Collection: {settings.QDRANT_COLLECTION_NAME}")
    
    # Confirm before proceeding
    response = input("\nThis will reindex ALL resumes. Continue? (yes/no): ").lower().strip()
    if response != 'yes':
        print("Reindexing cancelled.")
        return
    
    # Connect to database
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        await reindex_all_resumes(db)
    
    await engine.dispose()
    
    # Verify
    await verify_indexing()
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())