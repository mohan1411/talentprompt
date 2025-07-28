#!/usr/bin/env python3
"""Test API endpoints directly."""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8001"
TEST_USER_EMAIL = "promtitude@gmail.com"
TEST_USER_PASSWORD = "your_password_here"  # Update this


def test_health():
    """Test if API is running."""
    print("Testing API health...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print("✓ API is running")
        else:
            print("✗ API returned:", response.text)
    except Exception as e:
        print(f"✗ Cannot connect to API: {e}")
        return False
    return True


def test_login():
    """Test login and get token."""
    print("\nTesting login...")
    try:
        # Try form data login
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={
                "username": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print("✓ Login successful")
            return token_data.get("access_token")
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Try JSON login
            print("\nTrying JSON format...")
            response = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD
                }
            )
            
            if response.status_code == 200:
                token_data = response.json()
                print("✓ Login successful (JSON)")
                return token_data.get("access_token")
            else:
                print(f"✗ JSON login also failed: {response.text}")
                
    except Exception as e:
        print(f"✗ Login error: {e}")
    return None


def test_resumes(token=None):
    """Test resume endpoint."""
    print("\nTesting resume endpoint...")
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        # Test without auth first
        print("Testing without auth...")
        response = requests.get(f"{BASE_URL}/api/v1/resumes/?skip=0&limit=10")
        print(f"Without auth: {response.status_code}")
        
        if response.status_code == 401:
            print("✓ Correctly requires authentication")
        else:
            print(f"Response: {response.text[:200]}...")
        
        # Test with auth if we have token
        if token:
            print("\nTesting with auth...")
            response = requests.get(
                f"{BASE_URL}/api/v1/resumes/?skip=0&limit=10",
                headers=headers
            )
            print(f"With auth: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Got {len(data)} resumes")
                if data:
                    print(f"First resume: {data[0].get('first_name')} {data[0].get('last_name')}")
            else:
                print(f"✗ Error: {response.text}")
                
    except Exception as e:
        print(f"✗ Resume endpoint error: {e}")


def test_current_user(token):
    """Test current user endpoint."""
    print("\nTesting current user endpoint...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/users/me",
            headers=headers
        )
        
        if response.status_code == 200:
            user = response.json()
            print(f"✓ Current user: {user.get('email')}")
            print(f"  User ID: {user.get('id')}")
        else:
            print(f"✗ Error: {response.text}")
            
    except Exception as e:
        print(f"✗ Current user error: {e}")


def main():
    """Run all tests."""
    print("="*60)
    print("API TEST SUITE")
    print("="*60)
    print(f"Testing API at: {BASE_URL}")
    print(f"Test user: {TEST_USER_EMAIL}")
    
    # Test if API is running
    if not test_health():
        print("\n⚠️  API is not running!")
        print("Start it with: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001")
        return
    
    # Test login
    token = test_login()
    
    if not token:
        print("\n⚠️  Cannot proceed without authentication")
        print("Please update TEST_USER_PASSWORD in this script")
        return
    
    # Test other endpoints
    test_current_user(token)
    test_resumes(token)
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    # Update the password before running
    print("⚠️  Please update TEST_USER_PASSWORD in the script before running!")
    print("   Edit line 10: TEST_USER_PASSWORD = 'your_actual_password'")
    print("\nOr press Enter to continue with the placeholder password...")
    input()
    
    main()