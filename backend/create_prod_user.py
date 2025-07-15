#!/usr/bin/env python3
"""Create a user via the production API."""

import requests
import json

# Production API URL
API_URL = "https://talentprompt-production.up.railway.app/api/v1"

def create_user():
    """Create a new user via the API."""
    
    # User data
    user_data = {
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    }
    
    # First try to register the user
    print("Creating user via API...")
    response = requests.post(
        f"{API_URL}/auth/register",
        json=user_data
    )
    
    if response.status_code == 200:
        print(f"✅ User created successfully!")
        print(f"Email: {user_data['email']}")
        print(f"Password: {user_data['password']}")
    elif response.status_code == 400:
        error = response.json()
        if "already registered" in error.get("detail", "").lower():
            print("❌ User already exists. Try logging in with:")
            print(f"Email: {user_data['email']}")
            print(f"Password: {user_data['password']}")
        else:
            print(f"❌ Error: {error}")
    else:
        print(f"❌ Failed to create user: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    create_user()