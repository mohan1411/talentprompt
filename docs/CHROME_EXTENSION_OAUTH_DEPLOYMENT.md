# Chrome Extension OAuth Authentication - Production Deployment Guide

## Overview
This guide covers the deployment of OAuth user authentication for the Promtitude Chrome Extension.

## Production Configuration

### 1. Backend Configuration

#### Environment Variables
Add to your production `.env`:
```bash
# Extension Token Settings
EXTENSION_TOKEN_LENGTH=6
EXTENSION_TOKEN_EXPIRE_SECONDS=600  # 10 minutes
EXTENSION_TOKEN_RATE_LIMIT=3  # Max attempts per hour

# Redis Configuration (Required)
REDIS_URL=redis://your-redis-host:6379/0
```

#### CORS Configuration
Update `app/main.py` to ensure Chrome extensions are allowed:
```python
# The regex pattern in CORS middleware already handles this:
allow_origin_regex="chrome-extension://.*"
```

### 2. Frontend Configuration

#### Extension Auth Page
The extension auth page is available at:
- Production: `https://promtitude.com/extension-auth`
- Provides access code generation for OAuth users

#### Profile Page Integration
OAuth users see the Chrome Extension section with access code generation.

### 3. Chrome Extension Configuration

#### Update API URLs
In `popup/popup.js` and `background/service-worker.js`:
```javascript
const API_BASE_URL = 'https://talentprompt-production.up.railway.app/api/v1';
const API_URL = API_BASE_URL;  // Use production URL
```

#### Manifest Permissions
Ensure production manifest includes:
```json
"host_permissions": [
  "https://*.linkedin.com/*",
  "https://promtitude.com/*",
  "https://talentprompt-production.up.railway.app/*"
]
```

## Security Considerations

1. **Redis Availability**: Ensure Redis is highly available in production
2. **SSL/TLS**: All API endpoints must use HTTPS
3. **Rate Limiting**: Monitor for abuse and adjust limits if needed
4. **Monitoring**: Set up alerts for:
   - High failure rates
   - Unusual token generation patterns
   - Redis connection issues

## User Flow

1. **OAuth User Login**:
   - User navigates to `/extension-auth` or profile page
   - Generates 6-character access code (valid for 10 minutes)
   - Enters email and access code in extension
   - Extension receives JWT token (valid for 8 days)

2. **Subsequent Usage**:
   - Extension checks stored JWT on startup
   - No new access code needed until JWT expires
   - Logout clears JWT, requiring new access code

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Verify the regex pattern is in place
   - Check browser console for specific origin

2. **Token Not Working**
   - Verify Redis connectivity
   - Check token hasn't expired (10 min limit)
   - Ensure one-time use (can't reuse tokens)

3. **JWT Expiration**
   - Default is 8 days (11,520 minutes)
   - Adjust `ACCESS_TOKEN_EXPIRE_MINUTES` if needed

### Debug Logging
Enable debug logging in production carefully:
```python
logger.info(f"Token verification for {email}: success={result}")
```

## Monitoring Recommendations

1. **Metrics to Track**:
   - Access codes generated per hour/day
   - Success vs failure rate
   - Average time from generation to use
   - JWT token expiration patterns

2. **Alerts to Set**:
   - Redis connection failures
   - High rate of failed verifications
   - Unusual spike in token generation

## Future Enhancements

1. **Email Notifications**: Send email when access code is generated
2. **Device Management**: Allow users to see/revoke extension sessions
3. **Extended Sessions**: "Remember this device" for 30+ days
4. **Analytics**: Track extension usage patterns

## Rollback Plan

If issues arise:
1. OAuth users can still use the web interface
2. Revert CORS changes if extension connectivity fails
3. Clear Redis tokens if corruption suspected: `FLUSHDB` (use carefully)

## Support Documentation

Create user-facing help at `/help/chrome-extension-oauth`:
- Why access codes are needed
- Step-by-step login process
- Troubleshooting tips
- FAQ section