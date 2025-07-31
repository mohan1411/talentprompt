#!/usr/bin/env python3
"""Simple OAuth helper that uses the dev endpoint."""

import requests
import webbrowser
import urllib.parse

def main():
    print("="*60)
    print("SIMPLE OAUTH HELPER")
    print("="*60)
    
    # First, ensure the dev endpoint is available
    print("\nThis helper requires the dev endpoint to be added to your API.")
    print("Have you added the dev_oauth endpoint to your API? (y/n): ", end="")
    
    response = input().strip().lower()
    if response != 'y':
        print("\nPlease add the following to backend/app/api/v1/api.py:")
        print("1. Import: from app.api.v1.endpoints import dev_oauth")
        print("2. Add route: api_router.include_router(dev_oauth.router, prefix=\"/auth\", tags=[\"dev\"])")
        print("\nThen restart your backend and run this script again.")
        return
    
    email = input("\nEnter email (or press Enter for promtitude@gmail.com): ").strip()
    if not email:
        email = "promtitude@gmail.com"
    
    print(f"\nGenerating token for: {email}")
    
    # Call the dev endpoint
    try:
        response = requests.post(
            f"http://localhost:8001/api/v1/auth/dev/generate-oauth-token?email={email}"
        )
        
        if response.status_code != 200:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        token = data["access_token"]
        user = data["user"]
        
        print(f"\n✅ Token generated successfully!")
        print(f"   User ID: {user['id']}")
        print(f"   Name: {user.get('full_name', 'N/A')}")
        
        # Create OAuth callback URL
        callback_base = "http://localhost:3000/auth/callback"
        params = {
            "token": token,
            "state": "oauth_login"
        }
        
        callback_url = f"{callback_base}?{urllib.parse.urlencode(params)}"
        
        print("\n" + "="*60)
        print("OPTION 1: Automatic (Opens in browser)")
        print("="*60)
        print("Press Enter to open the OAuth callback URL in your browser...")
        print("This will simulate a successful OAuth login.")
        input()
        
        webbrowser.open(callback_url)
        print("✓ Opened in browser!")
        
        print("\n" + "="*60)
        print("OPTION 2: Manual Browser")
        print("="*60)
        print("Copy and paste this URL in your browser:")
        print(callback_url)
        
        print("\n" + "="*60)
        print("OPTION 3: Direct Console (If callback doesn't work)")
        print("="*60)
        print("Run this in your browser console:")
        print(f"""
localStorage.setItem('access_token', '{token}');
window.location.href = '/dashboard';
""")
        
        print("\n✅ Done! Check your browser.")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to backend at http://localhost:8001")
        print("Make sure your backend is running with: cd backend && uvicorn app.main:app --reload --port 8001")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()