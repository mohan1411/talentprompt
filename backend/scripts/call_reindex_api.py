#!/usr/bin/env python3
"""Call the security reindex API endpoint."""

import requests
import json
import getpass

def call_reindex_api():
    """Call the reindex API endpoint."""
    print("Security Reindex via API")
    print("=" * 60)
    
    # API URL
    base_url = "https://talentprompt-production.up.railway.app"
    
    # Get credentials
    email = input("Enter your email: ")
    password = getpass.getpass("Enter your password: ")
    
    # Login to get token
    print("\nLogging in...")
    login_response = requests.post(
        f"{base_url}/api/v1/auth/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"username={email}&password={password}"
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print("✅ Login successful")
    
    # Call reindex endpoint
    print("\nCalling security reindex endpoint...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    reindex_response = requests.post(
        f"{base_url}/api/v1/admin/security-reindex-vectors",
        headers=headers
    )
    
    if reindex_response.status_code == 200:
        result = reindex_response.json()
        print("\n✅ Reindex completed successfully!")
        print(f"Total resumes: {result.get('total_resumes', 0)}")
        print(f"Successfully reindexed: {result.get('success_count', 0)}")
        print(f"Errors: {result.get('error_count', 0)}")
        
        if result.get('errors'):
            print("\nErrors encountered:")
            for error in result['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
    else:
        print(f"❌ Reindex failed: {reindex_response.status_code}")
        print(reindex_response.text)
    
    print("\n" + "=" * 60)
    print("IMPORTANT: Test in production to verify users can only see their own resumes!")
    print("=" * 60)


if __name__ == "__main__":
    call_reindex_api()