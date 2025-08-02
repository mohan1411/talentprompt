#!/usr/bin/env python3
"""
Check Qdrant connection status in production.
Run this script to verify if Qdrant is properly connected.
"""

import requests
import json
import sys
from datetime import datetime


def check_qdrant_health(base_url="https://talentprompt-production.up.railway.app"):
    """Check Qdrant health via API endpoints."""
    
    print(f"🔍 Checking Qdrant connection at {base_url}")
    print("=" * 60)
    
    # Check general health
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Health: {data.get('status', 'unknown')}")
            print(f"   Version: {data.get('version', 'unknown')}")
        else:
            print(f"❌ API Health Check Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach API: {e}")
        return False
    
    # Check specific Qdrant health endpoint
    print("\n📊 Qdrant Status:")
    try:
        response = requests.get(f"{base_url}/api/v1/health/qdrant", timeout=10)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            
            if status == 'healthy':
                print(f"✅ Qdrant Status: {status}")
                print(f"   Message: {data.get('message', '')}")
            elif status == 'warning':
                print(f"⚠️  Qdrant Status: {status}")
                print(f"   Message: {data.get('message', '')}")
            else:
                print(f"❌ Qdrant Status: {status}")
                print(f"   Message: {data.get('message', '')}")
                
            print(f"   Timestamp: {data.get('timestamp', '')}")
        else:
            print(f"❌ Qdrant Health Check Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking Qdrant: {e}")
    
    # Try to perform a test search to verify full functionality
    print("\n🔍 Testing Vector Search Functionality:")
    try:
        # First, we need to get an auth token (you'll need valid credentials)
        # This is just a test to see if the search endpoint is responsive
        response = requests.post(
            f"{base_url}/api/v1/search/resumes",
            json={
                "query": "test search",
                "filters": {}
            },
            timeout=10
        )
        
        if response.status_code == 401:
            print("⚠️  Search endpoint requires authentication (expected)")
            print("   This means the endpoint is available but protected")
        elif response.status_code == 200:
            print("✅ Search endpoint is responsive")
        else:
            print(f"❓ Search endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing search: {e}")
    
    print("\n" + "=" * 60)
    print("📌 Summary:")
    print("   - Check your Railway logs for Qdrant connection details")
    print("   - Ensure QDRANT_URL environment variable is set correctly")
    print("   - For cloud Qdrant, ensure QDRANT_API_KEY is set")
    print("   - The application will fall back to keyword search if Qdrant is unavailable")


def check_local_qdrant():
    """Check if Qdrant is running locally (for development)."""
    print("\n🏠 Checking Local Qdrant (http://localhost:6333):")
    try:
        response = requests.get("http://localhost:6333", timeout=5)
        if response.status_code == 200:
            print("✅ Local Qdrant is running")
            
            # Check collections
            response = requests.get("http://localhost:6333/collections", timeout=5)
            if response.status_code == 200:
                data = response.json()
                collections = data.get('result', {}).get('collections', [])
                print(f"   Collections: {collections}")
        else:
            print("❌ Local Qdrant is not responding")
    except Exception as e:
        print("❌ Local Qdrant is not running")


if __name__ == "__main__":
    # Check production by default
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://talentprompt-production.up.railway.app"
    
    check_qdrant_health(base_url)
    
    # Also check local if running on dev machine
    if "localhost" not in base_url:
        check_local_qdrant()