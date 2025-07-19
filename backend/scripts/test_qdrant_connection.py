#!/usr/bin/env python3
"""Test Qdrant connection in production."""

import os
import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_qdrant_connection():
    """Test if we can connect to Qdrant."""
    print("Testing Qdrant Connection")
    print("=" * 60)
    
    # Check environment variables
    qdrant_url = os.getenv("QDRANT_URL", "not set")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", "not set")
    
    print(f"QDRANT_URL: {qdrant_url}")
    print(f"QDRANT_API_KEY: {'***' + qdrant_api_key[-4:] if qdrant_api_key != 'not set' else 'not set'}")
    
    if qdrant_url == "not set":
        print("\n❌ ERROR: QDRANT_URL environment variable is not set!")
        print("Please set it in Railway environment variables")
        return
    
    # Try to import and initialize
    try:
        from qdrant_client import QdrantClient
        print("\n✅ Qdrant client imported successfully")
        
        # Try to create client
        if "localhost" in qdrant_url or "127.0.0.1" in qdrant_url:
            print(f"\n⚠️  WARNING: Using localhost URL in production: {qdrant_url}")
            client = QdrantClient(host="localhost", port=6333)
        else:
            print(f"\nConnecting to Qdrant Cloud at: {qdrant_url}")
            client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key if qdrant_api_key != "not set" else None,
                timeout=30
            )
        
        # Test connection
        print("\nTesting connection...")
        collections = client.get_collections()
        print(f"✅ Connected successfully!")
        print(f"Found {len(collections.collections)} collections")
        
        for collection in collections.collections:
            print(f"  - {collection.name}")
            
    except Exception as e:
        print(f"\n❌ ERROR: Failed to connect to Qdrant")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
        if "getaddrinfo failed" in str(e):
            print("\n🔍 DIAGNOSIS: DNS resolution failed")
            print("Possible causes:")
            print("1. QDRANT_URL is set to 'localhost' or '127.0.0.1' in production")
            print("2. The Qdrant Cloud URL is incorrect")
            print("3. Network connectivity issues")
            
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    test_qdrant_connection()