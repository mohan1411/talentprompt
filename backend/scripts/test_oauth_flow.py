#!/usr/bin/env python3
"""Test the OAuth flow for Promtitude."""

import requests
import webbrowser
import json

def test_oauth_flow():
    base_url = "http://localhost:8001/api/v1"
    
    print("Testing OAuth flow for Promtitude...")
    print("=" * 50)
    
    # Step 1: Get OAuth URL
    print("\n1. Getting OAuth URL...")
    response = requests.get(f"{base_url}/auth/oauth/google/login")
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return
    
    oauth_data = response.json()
    auth_url = oauth_data['auth_url']
    state = oauth_data['state']
    
    print(f"   Auth URL: {auth_url}")
    print(f"   State: {state}")
    
    # Step 2: Open in browser
    print("\n2. Opening OAuth URL in browser...")
    print("   Please select a user in the browser window.")
    webbrowser.open(auth_url)
    
    print("\n3. After selecting a user, you will be redirected to the frontend.")
    print("   The frontend will handle the token and log you in.")
    
    print("\nAvailable OAuth users:")
    print("   - promtitude@gmail.com")
    print("   - taskmasterai1411@gmail.com")
    print("   - mohan.g1411@gmail.com")
    
    print("\nOAuth flow test complete!")

if __name__ == "__main__":
    test_oauth_flow()