# Simple OAuth Implementation Guide

This guide explains how to use the simple OAuth implementation that doesn't require authlib.

## Overview

We've implemented a simple OAuth system that allows existing OAuth users to authenticate without requiring the authlib library. This implementation includes:

1. **Mock OAuth endpoints** for testing
2. **Dev token generation** for existing users
3. **Frontend callback page** to handle OAuth responses
4. **Test scripts** to facilitate testing

## Prerequisites

1. Ensure `ALLOW_DEV_ENDPOINTS=true` is set in your backend `.env` file
2. Backend must be running on port 8001
3. Frontend must be running on port 3000

## Quick Start

### Option 1: Using the Test Script

```bash
cd backend
python scripts/test_simple_oauth.py
```

This script provides several options:
1. Create a test OAuth user
2. Test mock OAuth login
3. Test Google OAuth flow (mock)
4. Generate dev token for existing user

### Option 2: Using the Simple OAuth Helper

```bash
cd backend
python scripts/simple_oauth_helper.py
```

This will:
1. Generate a token for the specified user (default: promtitude@gmail.com)
2. Open the OAuth callback URL in your browser
3. Automatically log you in

### Option 3: Direct API Calls

1. **Create an OAuth test user:**
```bash
curl "http://localhost:8001/api/v1/oauth/test/create-oauth-user?email=test@example.com&provider=google"
```

2. **Mock OAuth login:**
```bash
curl -X POST "http://localhost:8001/api/v1/oauth/mock/login?email=test@example.com"
```

3. **Generate dev token (for any existing user):**
```bash
curl -X POST "http://localhost:8001/api/v1/auth/dev/generate-oauth-token?email=user@example.com"
```

## How It Works

### Backend Endpoints

1. **`/api/v1/oauth/google/login`** - Initiates Google OAuth flow (returns mock URL)
2. **`/api/v1/oauth/google/callback`** - Handles OAuth callback (validates user and returns token)
3. **`/api/v1/oauth/mock/login`** - Direct OAuth login for testing
4. **`/api/v1/oauth/test/create-oauth-user`** - Creates test OAuth users
5. **`/api/v1/auth/dev/generate-oauth-token`** - Generates tokens for any existing user

### Frontend Flow

1. User clicks "Continue with Google" on login page
2. Frontend calls `/api/v1/oauth/google/login` to get OAuth URL
3. User is redirected to Google (or mock endpoint)
4. After authentication, user is redirected to `/auth/callback` with token
5. Frontend stores token and fetches user data
6. User is redirected to dashboard

## Important Notes

- This implementation is for development/testing only
- In production, you would need proper OAuth integration with real providers
- The mock implementation only works with existing users in the database
- OAuth users are pre-verified (no email verification required)

## Troubleshooting

1. **"User not found" error**: Make sure the user exists in the database
2. **"Not an OAuth user" error**: The user must have `oauth_provider` set in the database
3. **Dev endpoints not working**: Ensure `ALLOW_DEV_ENDPOINTS=true` is set in backend `.env`
4. **Token generation fails**: Check that the backend is running and accessible

## Example: Login with promtitude@gmail.com

```bash
# Option 1: Use the helper script
cd backend
python scripts/simple_oauth_helper.py
# Press Enter to use default email (promtitude@gmail.com)
# Browser will open with authenticated session

# Option 2: Use the test script
cd backend
python scripts/test_simple_oauth.py
# Choose option 2 (Test mock OAuth login)
# Enter: promtitude@gmail.com
# Browser will open with authenticated session
```