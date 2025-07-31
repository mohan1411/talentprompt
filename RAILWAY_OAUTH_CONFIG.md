# Railway OAuth Configuration Guide

## Current Issue
OAuth login fails because the redirect URIs don't match between authorization and token exchange.

## Correct Railway Environment Variables

### Remove or Update This Variable:
```bash
# REMOVE THIS (or change it to backend URL):
GOOGLE_REDIRECT_URI=https://promtitude.com/auth/google/callback
```

### Required Variables:
```bash
# Frontend URL (keep as is)
FRONTEND_URL=https://promtitude.com

# Google OAuth credentials
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Environment
ENVIRONMENT=production
```

## Google Console Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services > Credentials
3. Click on your OAuth 2.0 Client ID
4. Add these **Authorized redirect URIs**:
   ```
   https://promtitude-backend-production.up.railway.app/api/v1/oauth/google/callback
   ```
   
   Remove any frontend URLs from the redirect URIs as they're not needed.

## How OAuth Flow Works

1. User clicks "Login with Google" on frontend
2. Frontend calls backend `/api/v1/auth/oauth/google/login`
3. Backend generates Google OAuth URL with redirect to **backend** callback
4. User authorizes on Google
5. Google redirects to **backend** `/api/v1/oauth/google/callback`
6. Backend exchanges code for user info
7. Backend creates/updates user
8. Backend redirects to **frontend** with JWT token

## Testing

After updating Railway variables and Google Console:

1. Clear browser cache/cookies
2. Go to https://promtitude.com
3. Click "Login with Google"
4. Should see Google consent screen
5. After authorization, should redirect back to promtitude.com with user logged in

## Debug Steps

1. Check Railway logs:
   ```bash
   railway logs
   ```

2. Look for these log messages:
   - "Google OAuth: Using redirect_uri: ..."
   - "Created new OAuth user: ..." or "Linked Google OAuth to existing user: ..."

3. If you see "redirect_uri_mismatch" error, ensure:
   - The redirect URI in Google Console matches exactly
   - No trailing slashes
   - HTTPS (not HTTP)
   - Correct backend URL

## Important Notes

- The `GOOGLE_REDIRECT_URI` environment variable should either be removed or set to the **backend** callback URL, not the frontend
- The backend handles the OAuth flow and redirects to the frontend after authentication
- All OAuth users are automatically verified (no email verification needed)