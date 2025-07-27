#!/usr/bin/env python3
"""Diagnose Qdrant vector search issues."""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qdrant_client import QdrantClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from app.core.config import settings
from app.models.resume import Resume
from app.services.vector_search import vector_search


async def check_qdrant_connection():
    """Check if we can connect to Qdrant."""
    print("1. Checking Qdrant connection...")
    
    try:
        # Initialize client
        qdrant_url = settings.QDRANT_URL
        qdrant_api_key = settings.QDRANT_API_KEY
        
        print(f"   - Qdrant URL: {qdrant_url}")
        print(f"   - API Key present: {'Yes' if qdrant_api_key else 'No'}")
        
        if qdrant_url and "localhost" not in qdrant_url and "127.0.0.1" not in qdrant_url:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=30)
        else:
            client = QdrantClient(host="localhost", port=6333, timeout=30)
        
        # Try to get collections
        collections = client.get_collections()
        print(f"   ✓ Connected to Qdrant successfully")
        print(f"   - Collections found: {len(collections.collections)}")
        
        for col in collections.collections:
            print(f"     • {col.name}")
        
        return client
        
    except Exception as e:
        print(f"   ✗ Failed to connect to Qdrant: {e}")
        return None


async def check_collection_status(client):
    """Check the status of our collection."""
    print("\n2. Checking collection status...")
    
    collection_name = settings.QDRANT_COLLECTION_NAME
    print(f"   - Collection name: {collection_name}")
    
    try:
        # Get collection info
        collection_info = client.get_collection(collection_name)
        
        print(f"   ✓ Collection exists")
        print(f"   - Points count: {collection_info.points_count}")
        print(f"   - Vector size: {collection_info.config.params.vectors.size}")
        print(f"   - Distance metric: {collection_info.config.params.vectors.distance}")
        
        # Check if empty
        if collection_info.points_count == 0:
            print("   ⚠️  WARNING: Collection is empty! No vectors indexed.")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ✗ Collection '{collection_name}' not found: {e}")
        return False


async def check_indexes(client):
    """Check if indexes exist."""
    print("\n3. Checking indexes...")
    
    collection_name = settings.QDRANT_COLLECTION_NAME
    
    try:
        # Get collection info
        collection_info = client.get_collection(collection_name)
        
        # Try to list indexed fields (this varies by qdrant version)
        print("   - Attempting to check indexed fields...")
        
        # Try a test search with user_id filter
        try:
            test_result = client.search(
                collection_name=collection_name,
                query_vector=[0.0] * 1536,
                query_filter={
                    "must": [{"key": "user_id", "match": {"value": "test"}}]
                },
                limit=1
            )
            print("   ✓ user_id index appears to be working")
        except Exception as e:
            if "index required" in str(e).lower():
                print("   ✗ user_id index is MISSING - this is the problem!")
                return False
            else:
                print(f"   ? Could not verify index: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error checking indexes: {e}")
        return False


async def check_database_resumes(db: AsyncSession):
    """Check how many resumes are in the database."""
    print("\n4. Checking database resumes...")
    
    try:
        # Count total resumes
        total = await db.execute(select(func.count(Resume.id)))
        total_count = total.scalar()
        print(f"   - Total resumes in database: {total_count}")
        
        # Count by user
        user_counts = await db.execute(
            select(Resume.user_id, func.count(Resume.id))
            .group_by(Resume.user_id)
        )
        
        print("   - Resumes per user:")
        for user_id, count in user_counts:
            print(f"     • User {user_id}: {count} resumes")
        
        # Get a sample resume
        sample = await db.execute(select(Resume).limit(1))
        sample_resume = sample.scalar_one_or_none()
        
        if sample_resume:
            print(f"\n   - Sample resume:")
            print(f"     • ID: {sample_resume.id}")
            print(f"     • Name: {sample_resume.first_name} {sample_resume.last_name}")
            print(f"     • Skills: {sample_resume.skills[:5] if sample_resume.skills else 'None'}")
            print(f"     • Vector indexed: {'Unknown' if not hasattr(sample_resume, 'vector_indexed') else sample_resume.vector_indexed}")
            return str(sample_resume.user_id)
        
        return None
        
    except Exception as e:
        print(f"   ✗ Error checking database: {e}")
        return None


async def test_vector_search(user_id: str):
    """Test vector search functionality."""
    print("\n5. Testing vector search...")
    
    queries = [
        "Python developer",
        "Senior engineer",
        "AWS",
        "developer"
    ]
    
    for query in queries:
        print(f"\n   Testing query: '{query}'")
        try:
            results = await vector_search.search_similar(
                query=query,
                user_id=user_id,
                limit=5
            )
            print(f"   - Results: {len(results)}")
            
            if results:
                print("   - Top result:")
                print(f"     • ID: {results[0]['resume_id']}")
                print(f"     • Score: {results[0]['score']:.3f}")
        except Exception as e:
            print(f"   ✗ Search failed: {e}")


async def check_sample_vectors(client):
    """Check a few vectors from the collection."""
    print("\n6. Checking sample vectors...")
    
    collection_name = settings.QDRANT_COLLECTION_NAME
    
    try:
        # Scroll through first few points
        points, _ = client.scroll(
            collection_name=collection_name,
            limit=3,
            with_payload=True,
            with_vectors=False
        )
        
        print(f"   - Found {len(points)} sample points:")
        for point in points:
            print(f"\n   Point ID: {point.id}")
            if point.payload:
                print(f"   - user_id: {point.payload.get('user_id', 'MISSING')}")
                print(f"   - resume_id: {point.payload.get('resume_id', 'MISSING')}")
                # Check for other fields
                other_fields = [k for k in point.payload.keys() if k not in ['user_id', 'resume_id']]
                if other_fields:
                    print(f"   - Other fields: {', '.join(other_fields[:5])}")
        
        if not points:
            print("   ⚠️  No vectors found in collection!")
            
    except Exception as e:
        print(f"   ✗ Error checking vectors: {e}")


async def suggest_fixes():
    """Suggest fixes based on diagnosis."""
    print("\n" + "="*60)
    print("DIAGNOSIS SUMMARY & RECOMMENDED FIXES")
    print("="*60)
    
    print("\nBased on the diagnosis, here are the recommended actions:")
    
    print("\n1. If collection is empty:")
    print("   - Run: python scripts/reindex_all_resumes.py")
    print("   - This will index all resumes from the database into Qdrant")
    
    print("\n2. If user_id index is missing:")
    print("   - Run: python scripts/fix_qdrant_indexes.py")
    print("   - This will create the necessary indexes")
    
    print("\n3. If Qdrant connection failed:")
    print("   - Check your QDRANT_URL and QDRANT_API_KEY in .env")
    print("   - Ensure Qdrant service is running")
    
    print("\n4. If vectors exist but search returns nothing:")
    print("   - Check that user_id in payload matches the search user_id")
    print("   - Verify embeddings are being generated correctly")


async def main():
    """Run full diagnosis."""
    print("="*60)
    print("QDRANT VECTOR SEARCH DIAGNOSIS")
    print("="*60)
    
    # Check Qdrant connection
    client = await check_qdrant_connection()
    if not client:
        await suggest_fixes()
        return
    
    # Check collection
    collection_exists = await check_collection_status(client)
    
    # Check indexes
    if collection_exists:
        indexes_ok = await check_indexes(client)
        await check_sample_vectors(client)
    
    # Check database
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        user_id = await check_database_resumes(db)
        
        # Test search if we have a user
        if user_id and collection_exists:
            await test_vector_search(user_id)
    
    await engine.dispose()
    
    # Provide recommendations
    await suggest_fixes()


if __name__ == "__main__":
    asyncio.run(main())