# Production OAuth Configuration Fix

## Issue
OAuth login in production redirects to localhost instead of the production domain.

## Root Cause
1. Backend environment variables not properly configured in Railway
2. Hardcoded localhost URLs in auth endpoints
3. Missing production backend URL configuration

## Solution Implemented

### 1. Code Changes
- Updated `/backend/app/api/v1/endpoints/auth.py` to use dynamic URLs based on request
- Updated `/backend/app/api/v1/endpoints/simple_oauth.py` to detect production environment
- Added proper URL handling for both development and production

### 2. Environment Variables Required in Railway

Set these environment variables in your Railway backend service:

```bash
# Required OAuth Configuration
FRONTEND_URL=https://promtitude.com
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
ENVIRONMENT=production

# Optional (if you want explicit control)
API_URL=https://promtitude-backend-production.up.railway.app
GOOGLE_REDIRECT_URI=https://promtitude-backend-production.up.railway.app/api/v1/oauth/google/callback
```

### 3. Google OAuth Console Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to APIs & Services > Credentials
4. Click on your OAuth 2.0 Client ID
5. Add these Authorized redirect URIs:
   - `https://promtitude-backend-production.up.railway.app/api/v1/oauth/google/callback`
   - `https://promtitude.com/auth/callback` (for frontend)
   - `https://promtitude.com/auth/google/callback`

### 4. Testing OAuth Flow

1. Clear browser cache and cookies
2. Go to https://promtitude.com
3. Click "Login with Google"
4. Should redirect to Google OAuth
5. After authorization, should redirect back to promtitude.com (not localhost)

## Temporary Workaround (if needed)

If the environment variables aren't updated yet, the code now includes a hardcoded production backend URL that will be used when `ENVIRONMENT=production` or when the frontend URL contains "promtitude".

## Verification Steps

1. Check Railway logs after deploying:
   ```
   railway logs
   ```

2. Verify environment variables are set:
   - In Railway dashboard, go to your backend service
   - Check Variables tab
   - Ensure FRONTEND_URL is set to https://promtitude.com

3. Test the OAuth endpoint directly:
   ```
   curl https://promtitude-backend-production.up.railway.app/api/v1/auth/oauth/google/login
   ```
   
   Should return an auth_url pointing to Google, not localhost.

## Notes

- The mock OAuth flow is only used in development when FRONTEND_URL contains "localhost"
- In production, it uses the proper Google OAuth flow
- OAuth states are stored in memory (should use Redis in production for scalability)