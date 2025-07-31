#!/usr/bin/env python3
"""Test the simple OAuth implementation."""

import requests
import webbrowser
import urllib.parse
import sys

def main():
    print("="*60)
    print("SIMPLE OAUTH TEST HELPER")
    print("="*60)
    
    # Base URLs
    api_base = "http://localhost:8001/api/v1"
    frontend_base = "http://localhost:3000"
    
    print("\nSelect an option:")
    print("1. Create a test OAuth user")
    print("2. Test mock OAuth login")
    print("3. Test Google OAuth flow (mock)")
    print("4. Generate dev token for existing user")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        # Create test OAuth user
        email = input("Enter email for new OAuth user (or press Enter for test@example.com): ").strip()
        if not email:
            email = "test@example.com"
        
        provider = input("Enter OAuth provider (google/linkedin, default: google): ").strip()
        if not provider:
            provider = "google"
        
        try:
            response = requests.get(
                f"{api_base}/oauth/test/create-oauth-user",
                params={"email": email, "provider": provider}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ {data['message']}")
                print(f"   User ID: {data['user']['id']}")
                print(f"   Email: {data['user']['email']}")
                print(f"   Provider: {data['user']['oauth_provider']}")
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    elif choice == "2":
        # Test mock OAuth login
        email = input("Enter OAuth user email: ").strip()
        if not email:
            print("Email is required!")
            return
        
        try:
            response = requests.post(
                f"{api_base}/oauth/mock/login",
                params={"email": email}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                user = data["user"]
                
                print(f"\n✅ Login successful!")
                print(f"   User: {user['full_name']} ({user['email']})")
                print(f"   Provider: {user['oauth_provider']}")
                
                # Create callback URL
                callback_url = f"{frontend_base}/auth/callback?" + urllib.parse.urlencode({
                    "access_token": token,
                    "token_type": "bearer",
                    "email": user["email"],
                    "name": user["full_name"]
                })
                
                print("\n" + "="*60)
                print("OPTION 1: Open in browser")
                print("="*60)
                input("Press Enter to open the callback URL in your browser...")
                webbrowser.open(callback_url)
                
                print("\n" + "="*60)
                print("OPTION 2: Manual")
                print("="*60)
                print("Copy this URL to your browser:")
                print(callback_url)
                
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(response.json().get("detail", response.text))
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    elif choice == "3":
        # Test Google OAuth flow
        print("\nInitiating Google OAuth flow...")
        
        try:
            response = requests.get(f"{api_base}/oauth/google/login")
            
            if response.status_code == 200:
                data = response.json()
                auth_url = data["auth_url"]
                state = data["state"]
                
                print(f"\n✅ OAuth URL generated!")
                print(f"   State: {state}")
                
                print("\nThis would normally redirect to Google for authentication.")
                print("For testing, we'll simulate a successful callback.")
                
                # Simulate callback
                input("\nPress Enter to simulate OAuth callback...")
                
                # Note: In a real scenario, Google would redirect back with a code
                # For testing, we're using a mock callback
                callback_params = {
                    "code": "mock_auth_code",
                    "state": state
                }
                
                callback_response = requests.get(
                    f"{api_base}/oauth/google/callback",
                    params=callback_params,
                    allow_redirects=False
                )
                
                if callback_response.status_code == 307:  # Redirect
                    redirect_url = callback_response.headers.get("Location")
                    print(f"\n✅ Callback processed!")
                    print(f"Redirect URL: {redirect_url}")
                    
                    input("\nPress Enter to open in browser...")
                    webbrowser.open(redirect_url)
                else:
                    print(f"\n❌ Error: {callback_response.status_code}")
                    print(callback_response.text)
                    
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    elif choice == "4":
        # Generate dev token
        email = input("Enter user email: ").strip()
        if not email:
            print("Email is required!")
            return
        
        try:
            response = requests.post(
                f"{api_base}/auth/dev/generate-oauth-token",
                params={"email": email}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                user = data["user"]
                
                print(f"\n✅ Token generated!")
                print(f"   User: {user['full_name']} ({user['email']})")
                print(f"   Active: {user['is_active']}")
                
                # Create callback URL
                callback_url = f"{frontend_base}/auth/callback?" + urllib.parse.urlencode({
                    "access_token": token,
                    "token_type": "bearer",
                    "email": user["email"],
                    "name": user["full_name"]
                })
                
                print("\n" + "="*60)
                print("Use this token in the Chrome extension or browser")
                print("="*60)
                input("Press Enter to open the callback URL in your browser...")
                webbrowser.open(callback_url)
                
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(response.json().get("detail", response.text))
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8001/api/v1/health")
        if response.status_code != 200:
            print("⚠️  Backend doesn't seem to be healthy!")
    except:
        print("❌ Could not connect to backend at http://localhost:8001")
        print("Make sure your backend is running with:")
        print("cd backend && uvicorn app.main:app --reload --port 8001")
        sys.exit(1)
    
    main()