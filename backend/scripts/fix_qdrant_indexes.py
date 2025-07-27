#!/usr/bin/env python3
"""Fix Qdrant collection indexes for user_id filtering."""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct
)

from app.core.config import settings


async def fix_qdrant_indexes():
    """Create necessary indexes on Qdrant collection."""
    print("Fixing Qdrant indexes...")
    
    # Initialize Qdrant client
    qdrant_url = settings.QDRANT_URL
    qdrant_api_key = settings.QDRANT_API_KEY
    
    if qdrant_url and "localhost" not in qdrant_url and "127.0.0.1" not in qdrant_url:
        # Cloud Qdrant
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=30
        )
    else:
        # Local Qdrant
        client = QdrantClient(
            host="localhost",
            port=6333,
            timeout=30
        )
    
    collection_name = settings.QDRANT_COLLECTION_NAME
    
    try:
        # Check if collection exists
        collections = client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)
        
        if not exists:
            print(f"Collection '{collection_name}' does not exist. Creating it...")
            # Create collection with proper configuration
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=1536,  # OpenAI ada-002 embeddings
                    distance=Distance.COSINE
                )
            )
            print(f"Created collection: {collection_name}")
        
        # Create index on user_id field
        print("\nCreating index on 'user_id' field...")
        try:
            # For older qdrant-client versions, use simpler syntax
            client.create_payload_index(
                collection_name=collection_name,
                field_name="user_id",
                field_schema="keyword"  # Simple string type for older versions
            )
            print("✓ Created keyword index on 'user_id'")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✓ Index on 'user_id' already exists")
            else:
                print(f"⚠ Error creating user_id index: {e}")
        
        # Create index on resume_id field
        print("\nCreating index on 'resume_id' field...")
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name="resume_id",
                field_schema="keyword"  # Simple string type for older versions
            )
            print("✓ Created keyword index on 'resume_id'")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✓ Index on 'resume_id' already exists")
            else:
                print(f"⚠ Error creating resume_id index: {e}")
        
        # Get collection info to verify
        print("\nVerifying collection configuration...")
        collection_info = client.get_collection(collection_name)
        
        print(f"\nCollection: {collection_name}")
        print(f"Vectors count: {collection_info.points_count}")
        print(f"Vectors config: {collection_info.config.params.vectors}")
        
        # Check payload schema
        if hasattr(collection_info.config, 'payload_schema') and collection_info.config.payload_schema:
            print("\nPayload indexes:")
            for field_name, field_config in collection_info.config.payload_schema.items():
                print(f"  - {field_name}: {field_config}")
        else:
            print("\nNo payload schema info available")
        
        print("\n✅ Qdrant indexes fixed successfully!")
        
        # Test the fix by doing a sample search
        print("\nTesting user_id filtering...")
        try:
            # Just test the filter, don't need actual results
            results = client.search(
                collection_name=collection_name,
                query_vector=[0.0] * 1536,  # Dummy vector
                query_filter={
                    "must": [
                        {
                            "key": "user_id",
                            "match": {
                                "value": "test-user-id"
                            }
                        }
                    ]
                },
                limit=1
            )
            print("✓ Filter test successful - indexes are working!")
        except Exception as e:
            print(f"⚠ Filter test failed: {e}")
            print("You may need to recreate the collection or contact Qdrant support.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure Qdrant is running")
        print("2. Check your QDRANT_URL and QDRANT_API_KEY in .env")
        print("3. If using Qdrant Cloud, ensure your API key has write permissions")
        return False
    
    return True


async def recreate_collection_if_needed():
    """Recreate collection with proper indexes if needed."""
    print("\n" + "="*60)
    print("OPTIONAL: Recreate Collection")
    print("="*60)
    print("\nIf the index creation didn't work, you may need to recreate the collection.")
    print("WARNING: This will DELETE all existing vectors!")
    
    response = input("\nDo you want to recreate the collection? (yes/no): ").lower().strip()
    
    if response == 'yes':
        # Initialize client
        qdrant_url = settings.QDRANT_URL
        qdrant_api_key = settings.QDRANT_API_KEY
        
        if qdrant_url and "localhost" not in qdrant_url and "127.0.0.1" not in qdrant_url:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=30)
        else:
            client = QdrantClient(host="localhost", port=6333, timeout=30)
        
        collection_name = settings.QDRANT_COLLECTION_NAME
        
        try:
            # Delete existing collection
            print(f"\nDeleting collection '{collection_name}'...")
            client.delete_collection(collection_name)
            print("✓ Collection deleted")
            
            # Recreate with proper configuration
            print(f"\nRecreating collection '{collection_name}'...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=1536,
                    distance=Distance.COSINE
                )
            )
            print("✓ Collection created")
            
            # Create indexes
            print("\nCreating indexes...")
            client.create_payload_index(
                collection_name=collection_name,
                field_name="user_id",
                field_schema="keyword"
            )
            print("✓ Created index on 'user_id'")
            
            client.create_payload_index(
                collection_name=collection_name,
                field_name="resume_id",
                field_schema="keyword"
            )
            print("✓ Created index on 'resume_id'")
            
            print("\n✅ Collection recreated successfully!")
            print("\n⚠️  IMPORTANT: You need to re-index all resumes now!")
            print("Run: python scripts/reindex_all_resumes.py")
            
        except Exception as e:
            print(f"\n❌ Error recreating collection: {e}")
    else:
        print("\nSkipping collection recreation.")


async def main():
    """Run the fix."""
    success = await fix_qdrant_indexes()
    
    if not success:
        await recreate_collection_if_needed()


if __name__ == "__main__":
    asyncio.run(main())