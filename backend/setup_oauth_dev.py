#!/usr/bin/env python3
"""Quick setup script for OAuth in development."""

import os
import sys
from pathlib import Path

def setup_oauth_dev():
    """Set up OAuth for development use."""
    print("OAuth Development Setup")
    print("=" * 60)
    
    # Check if .env file exists
    env_file = Path("../.env")
    if not env_file.exists():
        env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Creating a new .env file...")
        env_file = Path(".env")
    
    # Read existing .env content
    existing_content = ""
    if env_file.exists():
        with open(env_file, 'r') as f:
            existing_content = f.read()
    
    # Check for ALLOW_DEV_ENDPOINTS
    if "ALLOW_DEV_ENDPOINTS" not in existing_content:
        print("\n✅ Adding ALLOW_DEV_ENDPOINTS=true to .env file...")
        with open(env_file, 'a') as f:
            f.write("\n# Enable dev OAuth endpoint\n")
            f.write("ALLOW_DEV_ENDPOINTS=true\n")
    else:
        print("ℹ️  ALLOW_DEV_ENDPOINTS already in .env file")
    
    # Check for ENVIRONMENT setting
    if "ENVIRONMENT=" not in existing_content:
        print("✅ Adding ENVIRONMENT=development to .env file...")
        with open(env_file, 'a') as f:
            f.write("\n# Development environment\n")
            f.write("ENVIRONMENT=development\n")
    
    print("\n" + "=" * 60)
    print("OAuth Development Setup Complete!")
    print("\nNext steps:")
    print("1. Restart your backend server")
    print("2. Run: python scripts/simple_oauth_helper.py")
    print("3. Or run: python test_oauth_restoration.py to verify endpoints")
    
    print("\nFor production OAuth with Google/LinkedIn:")
    print("Add these to your .env file:")
    print("  GOOGLE_CLIENT_ID=your-google-client-id")
    print("  GOOGLE_CLIENT_SECRET=your-google-client-secret")
    print("  LINKEDIN_CLIENT_ID=your-linkedin-client-id")
    print("  LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret")


if __name__ == "__main__":
    setup_oauth_dev()