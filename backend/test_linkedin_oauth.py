#!/usr/bin/env python3
"""Test LinkedIn OAuth flow"""

import asyncio
import os
import sys
sys.path.insert(0, '.')

from app.core.config import settings
from app.services.oauth import oauth_service

async def test_linkedin_oauth():
    try:
        print(f"LinkedIn Client ID: {settings.LINKEDIN_CLIENT_ID}")
        print(f"LinkedIn Client Secret: {'*' * 10 if settings.LINKEDIN_CLIENT_SECRET else 'NOT SET'}")
        print(f"LinkedIn Redirect URI: {settings.LINKEDIN_REDIRECT_URI}")
        
        # Test if OAuth service can generate LinkedIn URL
        state = oauth_service.generate_state_token()
        auth_url = oauth_service.get_linkedin_auth_url(state)
        print(f"\nGenerated LinkedIn Auth URL:\n{auth_url}")
        
        # Test LinkedIn user info endpoint (with a fake code to see the error)
        print("\nTesting LinkedIn user info endpoint with fake code...")
        try:
            result = await oauth_service.get_linkedin_user_info("fake_code")
        except Exception as e:
            print(f"Expected error: {type(e).__name__}: {e}")
            
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_linkedin_oauth())