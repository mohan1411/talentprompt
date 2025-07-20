"""OAuth service for social login integration."""

import re
import secrets
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import httpx
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client import OAuthError

from app.core.config import settings
from app.schemas.user import UserCreate
import logging

logger = logging.getLogger(__name__)


class OAuthService:
    """Service for handling OAuth authentication flows."""
    
    def __init__(self):
        """Initialize OAuth clients."""
        self.oauth = OAuth()
        
        # Configure Google OAuth if credentials are provided
        if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            self.oauth.register(
                name='google',
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_kwargs={
                    'scope': 'openid email profile'
                }
            )
            logger.info("Google OAuth configured")
        else:
            logger.warning("Google OAuth not configured - missing credentials")
        
        # Configure LinkedIn OAuth if credentials are provided
        if settings.LINKEDIN_CLIENT_ID and settings.LINKEDIN_CLIENT_SECRET:
            self.oauth.register(
                name='linkedin',
                client_id=settings.LINKEDIN_CLIENT_ID,
                client_secret=settings.LINKEDIN_CLIENT_SECRET,
                access_token_url='https://www.linkedin.com/oauth/v2/accessToken',
                access_token_params=None,
                authorize_url='https://www.linkedin.com/oauth/v2/authorization',
                authorize_params=None,
                api_base_url='https://api.linkedin.com/v2/',
                client_kwargs={
                    'scope': 'openid profile email'
                }
            )
            logger.info("LinkedIn OAuth configured")
        else:
            logger.warning("LinkedIn OAuth not configured - missing credentials")
    
    def generate_state_token(self) -> str:
        """Generate a secure random state token for OAuth."""
        return secrets.token_urlsafe(32)
    
    def get_google_auth_url(self, state: str, redirect_uri: Optional[str] = None) -> str:
        """Get Google OAuth authorization URL."""
        if not hasattr(self.oauth, 'google'):
            raise ValueError("Google OAuth not configured")
        
        redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI or f"{settings.FRONTEND_URL}/auth/google/callback"
        
        params = {
            'response_type': 'code',
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'scope': 'openid email profile',
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        logger.info(f"Generated Google OAuth URL with redirect_uri: {redirect_uri}")
        logger.info(f"Full auth URL: {auth_url}")
        
        return auth_url
    
    def get_linkedin_auth_url(self, state: str, redirect_uri: Optional[str] = None) -> str:
        """Get LinkedIn OAuth authorization URL."""
        if not hasattr(self.oauth, 'linkedin'):
            raise ValueError("LinkedIn OAuth not configured")
        
        redirect_uri = redirect_uri or settings.LINKEDIN_REDIRECT_URI or f"{settings.FRONTEND_URL}/auth/linkedin/callback"
        
        params = {
            'response_type': 'code',
            'client_id': settings.LINKEDIN_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'scope': 'openid profile email',
            'state': state
        }
        
        return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    
    async def get_google_user_info(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """Exchange Google authorization code for user info."""
        redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI or f"{settings.FRONTEND_URL}/auth/google/callback"
        
        logger.info(f"Google OAuth: Using redirect_uri: {redirect_uri}")
        
        # Exchange code for token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        async with httpx.AsyncClient() as client:
            try:
                token_response = await client.post(token_url, data=token_data)
                token_response.raise_for_status()
                token_info = token_response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Google OAuth token exchange failed: {e.response.text}")
                raise ValueError(f"Failed to exchange code for token: {e.response.text}")
            
            # Get user info
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token_info['access_token']}"}
            )
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()
            
            logger.info(f"Google user info response: {user_info}")
            
            # Ensure we have required fields
            if 'id' not in user_info:
                raise ValueError(f"Missing 'id' in Google user info: {user_info}")
            if 'email' not in user_info:
                raise ValueError(f"Missing 'email' in Google user info: {user_info}")
            
            return {
                'provider': 'google',
                'provider_id': user_info['id'],
                'email': user_info['email'],
                'email_verified': user_info.get('verified_email', False),
                'name': user_info.get('name'),
                'given_name': user_info.get('given_name'),
                'family_name': user_info.get('family_name'),
                'picture': user_info.get('picture'),
                'raw_data': user_info
            }
    
    async def get_linkedin_user_info(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """Exchange LinkedIn authorization code for user info."""
        redirect_uri = redirect_uri or settings.LINKEDIN_REDIRECT_URI or f"{settings.FRONTEND_URL}/auth/linkedin/callback"
        
        # Exchange code for token
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        token_data = {
            'code': code,
            'client_id': settings.LINKEDIN_CLIENT_ID,
            'client_secret': settings.LINKEDIN_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            token_response.raise_for_status()
            token_info = token_response.json()
            
            # Get user info using OpenID Connect
            userinfo_response = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {token_info['access_token']}"}
            )
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()
            
            return {
                'provider': 'linkedin',
                'provider_id': user_info['sub'],
                'email': user_info['email'],
                'email_verified': user_info.get('email_verified', False),
                'name': user_info.get('name'),
                'given_name': user_info.get('given_name'),
                'family_name': user_info.get('family_name'),
                'picture': user_info.get('picture'),
                'raw_data': user_info
            }
    
    def create_user_from_oauth(self, oauth_data: Dict[str, Any]) -> UserCreate:
        """Create UserCreate schema from OAuth data."""
        # Generate username from email
        email = oauth_data['email']
        username = re.sub(r'[^a-z0-9]', '', email.split('@')[0].lower())
        
        # Ensure username is unique by adding random suffix if needed
        username = f"{username}_{secrets.token_hex(4)}"
        
        return UserCreate(
            email=email,
            username=username,
            password=secrets.token_urlsafe(32),  # Random password for OAuth users
            full_name=oauth_data.get('name'),
            is_active=True,
            is_verified=oauth_data.get('email_verified', False)
        )


# Singleton instance
oauth_service = OAuthService()