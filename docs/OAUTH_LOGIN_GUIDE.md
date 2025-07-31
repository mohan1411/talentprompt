# OAuth Login Guide for Promtitude

This guide explains how to use OAuth login functionality in Promtitude.

## Overview

OAuth login is now functional for existing OAuth users. The system uses a mock OAuth implementation that allows existing OAuth users to authenticate without requiring Google's actual OAuth flow.

## Available OAuth Users

The following OAuth users are available in the system:
- promtitude@gmail.com
- taskmasterai1411@gmail.com
- mohan.g1411@gmail.com

## How to Login with OAuth

### Option 1: Through the Web Interface

1. Go to http://localhost:3000/login
2. Click "Continue with Google"
3. You'll be redirected to a user selection page
4. Click on one of the available OAuth users
5. You'll be automatically logged in and redirected to the dashboard

### Option 2: Using the Test Script

```bash
cd backend
python scripts/test_oauth_flow.py
```

This will:
1. Get the OAuth URL
2. Open it in your browser
3. Allow you to select a user
4. Complete the authentication flow

### Option 3: Direct API Testing

1. Get OAuth URL:
```bash
curl http://localhost:8001/api/v1/auth/oauth/google/login
```

2. Visit the returned URL in your browser
3. Select a user to authenticate

## Technical Details

### Frontend Flow
1. User clicks "Continue with Google" on login page
2. Frontend calls `/api/v1/auth/oauth/google/login`
3. Backend returns mock OAuth URL
4. User is redirected to user selection page
5. User selects an account
6. Backend generates JWT token
7. User is redirected to `/auth/callback` with token
8. Frontend stores token and fetches user data
9. User is redirected to dashboard

### Backend Implementation
- Mock OAuth endpoints in `/backend/app/api/v1/endpoints/auth.py`
- No external dependencies (authlib not required)
- Works with existing OAuth users in database
- Generates standard JWT tokens

## Troubleshooting

### "User not found" Error
Make sure the user exists in the database. Only the three users listed above are available.

### Frontend Not Redirecting
Ensure both frontend (port 3000) and backend (port 8001) are running.

### Token Not Working
Check that the backend is properly started with:
```bash
cd backend
docker-compose ps
```

The backend should be running on port 8001.

## Production Considerations

This is a development-only implementation. In production:
- Implement real OAuth with Google/LinkedIn
- Use proper OAuth libraries (authlib)
- Configure proper redirect URLs
- Set up OAuth apps with providers