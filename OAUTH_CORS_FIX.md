# OAuth and CORS Configuration Fix

## Issue
"Failed to fetch" error when trying to login with OAuth - this is a CORS issue where the frontend cannot communicate with the backend.

## Root Causes
1. Frontend (Vercel) doesn't have the correct backend URL configured
2. Backend might not have all CORS origins properly set (fixed in code)

## Required Configuration

### 1. Vercel Environment Variables (Frontend)
Go to your Vercel project settings and set:

```bash
NEXT_PUBLIC_API_URL=https://promtitude-backend-production.up.railway.app
NEXT_PUBLIC_WS_URL=wss://promtitude-backend-production.up.railway.app
```

**Important**: After setting these, you need to redeploy the frontend for the changes to take effect.

### 2. Railway Environment Variables (Backend)
Ensure these are set:

```bash
# Frontend URL
FRONTEND_URL=https://promtitude.com

# Remove or update this to backend URL
# GOOGLE_REDIRECT_URI should be removed or set to:
# https://promtitude-backend-production.up.railway.app/api/v1/oauth/google/callback

# Environment
ENVIRONMENT=production

# Optional: Explicitly set CORS origins
BACKEND_CORS_ORIGINS=["https://promtitude.com","https://www.promtitude.com","https://promtitude.vercel.app"]
```

### 3. Google OAuth Console
Ensure this redirect URI is registered:
```
https://promtitude-backend-production.up.railway.app/api/v1/oauth/google/callback
```

## How to Debug

1. **Check Frontend API URL**:
   - Open browser console on https://promtitude.com
   - Type: `console.log(window.__NEXT_DATA__.runtimeConfig)`
   - Should show the correct API URL

2. **Test Backend CORS**:
   ```bash
   curl -X OPTIONS https://promtitude-backend-production.up.railway.app/api/v1/auth/oauth/google/login \
     -H "Origin: https://promtitude.com" \
     -H "Access-Control-Request-Method: GET" \
     -v
   ```
   Should return Access-Control-Allow-Origin header with https://promtitude.com

3. **Check Railway Logs**:
   ```bash
   railway logs
   ```
   Look for:
   - "✓ CORS configured correctly for promtitude.com"
   - Any OAuth error messages

## Quick Test

After configuration:
1. Clear browser cache/cookies
2. Open Network tab in browser DevTools
3. Click "Login with Google"
4. Check for:
   - Request to `/api/v1/auth/oauth/google/login`
   - Should return 200 with auth_url
   - No CORS errors in console

## OAuth Flow Diagram

```
1. Frontend (promtitude.com) 
   ↓ GET /api/v1/auth/oauth/google/login
2. Backend (Railway)
   ↓ Returns Google OAuth URL
3. User → Google OAuth
   ↓ Authorizes
4. Google → Backend callback (Railway)
   ↓ Exchanges code for user info
5. Backend → Frontend redirect
   ↓ With JWT token
6. Frontend → Logged in
```

## Common Issues

1. **"Failed to fetch"**: CORS issue - frontend can't reach backend
   - Fix: Set NEXT_PUBLIC_API_URL in Vercel

2. **"redirect_uri_mismatch"**: Google OAuth configuration issue
   - Fix: Add backend callback URL to Google Console

3. **"User not found"**: OAuth working but user creation failing
   - Check Railway logs for database errors

4. **Redirects to localhost**: Backend using wrong URLs
   - Fix: Set FRONTEND_URL in Railway