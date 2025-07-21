#!/usr/bin/env python3
"""Test OAuth configuration"""

import sys
sys.path.insert(0, '.')

try:
    from app.core.config import settings
    print(f"LinkedIn Client ID: {settings.LINKEDIN_CLIENT_ID}")
    print(f"LinkedIn Redirect URI: {settings.LINKEDIN_REDIRECT_URI}")
    
    from app.services.oauth import oauth_service
    print("OAuth service loaded successfully")
    
    # Test LinkedIn auth URL generation
    state = oauth_service.generate_state_token()
    print(f"Generated state: {state}")
    
    auth_url = oauth_service.get_linkedin_auth_url(state)
    print(f"LinkedIn auth URL: {auth_url}")
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()