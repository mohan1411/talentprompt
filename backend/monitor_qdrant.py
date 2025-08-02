#!/usr/bin/env python3
"""
Monitor Qdrant connection and status in production.
This script can be run inside the production container to check Qdrant status.
"""

import os
import sys
import asyncio
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


async def check_qdrant_connection():
    """Check Qdrant connection using the same configuration as the app."""
    
    # Get configuration from environment
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "promtitude_resumes")
    
    print(f"🔍 Qdrant Connection Monitor")
    print(f"{'=' * 60}")
    print(f"📅 Timestamp: {datetime.utcnow().isoformat()}")
    print(f"🌐 Qdrant URL: {qdrant_url}")
    print(f"🔑 API Key: {'Set' if qdrant_api_key else 'Not Set'}")
    print(f"📚 Collection: {collection_name}")
    print(f"{'=' * 60}\n")
    
    try:
        # Initialize client
        if "localhost" in qdrant_url or "127.0.0.1" in qdrant_url:
            print("📍 Using local Qdrant connection")
            client = QdrantClient(url=qdrant_url, timeout=30)
        else:
            print("☁️  Using cloud Qdrant connection")
            if not qdrant_api_key:
                print("❌ ERROR: QDRANT_API_KEY not set for cloud instance!")
                return False
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=30)
        
        # Test 1: Check if we can connect
        print("🧪 Test 1: Checking connection...")
        collections = client.get_collections()
        print(f"✅ Connected successfully!")
        print(f"   Collections found: {[c.name for c in collections.collections]}")
        
        # Test 2: Check specific collection
        print(f"\n🧪 Test 2: Checking collection '{collection_name}'...")
        try:
            collection_info = client.get_collection(collection_name)
            print(f"✅ Collection exists!")
            print(f"   Vectors count: {collection_info.points_count}")
            print(f"   Vectors size: {collection_info.config.params.vectors.size}")
            print(f"   Distance metric: {collection_info.config.params.vectors.distance}")
            
            # Check payload schema
            if collection_info.config.params.payload_schema:
                print(f"   Indexed fields: {list(collection_info.config.params.payload_schema.keys())}")
        except Exception as e:
            print(f"⚠️  Collection '{collection_name}' not found: {e}")
            print("   The app will create it automatically on first use")
        
        # Test 3: Try a simple operation
        print(f"\n🧪 Test 3: Testing basic operations...")
        try:
            # Count points
            count_result = client.count(
                collection_name=collection_name,
                exact=False  # Use approximate count for performance
            )
            print(f"✅ Can perform operations on collection")
            print(f"   Approximate vector count: {count_result.count}")
        except Exception as e:
            print(f"ℹ️  Collection operations not available yet: {e}")
        
        # Test 4: Check cluster health (if applicable)
        print(f"\n🧪 Test 4: Checking cluster health...")
        try:
            # This might not be available on all Qdrant versions
            cluster_info = client.get_cluster_info()
            print(f"✅ Cluster is healthy")
        except:
            print("ℹ️  Cluster info not available (single node or cloud instance)")
        
        print(f"\n{'=' * 60}")
        print("✅ QDRANT IS PROPERLY CONNECTED AND FUNCTIONAL")
        print(f"{'=' * 60}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to connect to Qdrant")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        print(f"\n🔧 Troubleshooting:")
        print(f"   1. Check if Qdrant container is running: docker ps | grep qdrant")
        print(f"   2. Check Qdrant logs: docker logs <qdrant-container-id>")
        print(f"   3. Verify QDRANT_URL is correct in Railway environment variables")
        print(f"   4. For cloud Qdrant, ensure QDRANT_API_KEY is set")
        print(f"   5. Check network connectivity from Railway to Qdrant")
        
        print(f"\n{'=' * 60}")
        print("❌ QDRANT CONNECTION FAILED")
        print(f"{'=' * 60}")
        
        return False


async def test_from_app_service():
    """Test using the actual VectorSearchService from the app."""
    print(f"\n\n🔄 Testing via Application Service...")
    print(f"{'=' * 60}")
    
    try:
        from app.services.vector_search import vector_search
        
        # Get collection info
        info = await vector_search.get_collection_info()
        
        if info["status"] == "connected":
            print("✅ VectorSearchService is connected")
            print(f"   Collection: {info['collection_name']}")
            print(f"   Points count: {info['points_count']}")
        else:
            print("❌ VectorSearchService connection failed")
            print(f"   Error: {info.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Failed to test via app service: {e}")


def main():
    """Run all Qdrant checks."""
    # Run async checks
    loop = asyncio.get_event_loop()
    
    # Basic connection check
    connected = loop.run_until_complete(check_qdrant_connection())
    
    # If connected, also test via app service
    if connected:
        loop.run_until_complete(test_from_app_service())
    
    # Exit with appropriate code
    sys.exit(0 if connected else 1)


if __name__ == "__main__":
    main()