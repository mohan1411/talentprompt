# OAuth Setup Guide

This guide will help you set up Google and LinkedIn OAuth for the Promtitude platform.

## Prerequisites

- Backend server running on `http://localhost:8000`
- Frontend server running on `http://localhost:3000`
- Google Cloud Console account
- LinkedIn Developer account

## Google OAuth Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google+ API (or Google Identity API)

2. **Configure OAuth Consent Screen**
   - Navigate to APIs & Services > OAuth consent screen
   - Choose "External" for user type
   - Fill in the required fields:
     - App name: Promtitude
     - User support email: your-email@example.com
     - Developer contact: your-email@example.com
   - Add scopes: `email`, `profile`, `openid`

3. **Create OAuth Credentials**
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - Development: `http://localhost:3000/auth/google/callback`
     - Production: `https://yourdomain.com/auth/google/callback`
   - Save the Client ID and Client Secret

## LinkedIn OAuth Setup

1. **Create a LinkedIn App**
   - Go to [LinkedIn Developers](https://www.linkedin.com/developers/apps)
   - Click "Create app"
   - Fill in the required information:
     - App name: Promtitude
     - LinkedIn Page: Select or create a company page
     - App logo: Upload your logo
     - Legal agreement: Accept terms

2. **Configure OAuth Settings**
   - In your app settings, go to "Auth" tab
   - Add Authorized redirect URLs:
     - Development: `http://localhost:3000/auth/linkedin/callback`
     - Production: `https://yourdomain.com/auth/linkedin/callback`
   - Request access to Sign In with LinkedIn products

3. **Get Credentials**
   - In the "Auth" tab, copy:
     - Client ID
     - Client Secret

## Environment Configuration

1. **Backend Configuration**
   Create or update `.env` file in the backend directory:
   ```bash
   # Google OAuth
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
   
   # LinkedIn OAuth
   LINKEDIN_CLIENT_ID=your-linkedin-client-id
   LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
   LINKEDIN_REDIRECT_URI=http://localhost:3000/auth/linkedin/callback
   
   # Frontend URL
   FRONTEND_URL=http://localhost:3000
   ```

2. **Frontend Configuration**
   Create or update `.env.local` file in the frontend directory:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

## Testing OAuth Flow

1. **Run Database Migrations**
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **Start Backend Server**
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Start Frontend Server**
   ```bash
   cd frontend
   npm run dev
   ```

4. **Test OAuth Login**
   - Navigate to `http://localhost:3000/login`
   - Click "Continue with Google" or "Continue with LinkedIn"
   - Complete the OAuth flow
   - Verify you're redirected to the dashboard

## Troubleshooting

### Common Issues

1. **"Invalid redirect URI" error**
   - Ensure the redirect URI in your OAuth provider matches exactly
   - Check for trailing slashes
   - Verify protocol (http vs https)

2. **"OAuth not configured" error**
   - Check that all environment variables are set
   - Restart both backend and frontend servers after adding env vars

3. **CORS errors**
   - Ensure FRONTEND_URL is correctly set in backend
   - Check that CORS middleware is properly configured

### Debug Tips

1. Check backend logs for OAuth errors:
   ```bash
   tail -f backend/logs/app.log
   ```

2. Use browser developer tools to inspect:
   - Network requests during OAuth flow
   - Console errors
   - Local/session storage for OAuth state

3. Test OAuth endpoints directly:
   ```bash
   # Get OAuth URL
   curl http://localhost:8000/api/v1/auth/oauth/google/login
   ```

## Production Deployment

When deploying to production:

1. Update redirect URIs in OAuth providers to use your production domain
2. Use HTTPS for all OAuth callbacks
3. Update environment variables with production values
4. Consider using a secrets management service for OAuth credentials
5. Enable rate limiting on OAuth endpoints
6. Monitor OAuth error rates and success metrics

## Security Best Practices

1. **Never commit OAuth credentials to version control**
2. **Use different OAuth apps for development and production**
3. **Regularly rotate OAuth client secrets**
4. **Implement PKCE for additional security (if supported)**
5. **Monitor for suspicious OAuth activity**
6. **Implement rate limiting on OAuth endpoints**