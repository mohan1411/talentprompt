#!/usr/bin/env python3
"""Test if the backend server is running and accessible."""

import requests
import json

def test_server():
    """Test various endpoints."""
    base_url = "http://localhost:8000"
    
    print("\n" + "="*60)
    print("TESTING BACKEND SERVER")
    print("="*60)
    
    # Test root endpoint
    try:
        print(f"\n1. Testing root endpoint: {base_url}/")
        response = requests.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ERROR: Server not running or not accessible: {e}")
        return False
    
    # Test health endpoint
    try:
        print(f"\n2. Testing health endpoint: {base_url}/health")
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test the debug email endpoint
    try:
        print(f"\n3. Testing email debug endpoint: {base_url}/test-email-debug")
        response = requests.get(f"{base_url}/test-email-debug")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n" + "="*60)
    print("Server is running and accessible!")
    print("="*60)
    return True

if __name__ == "__main__":
    test_server()