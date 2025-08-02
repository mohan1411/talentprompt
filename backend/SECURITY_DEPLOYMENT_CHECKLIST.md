# Security Deployment Checklist for Promtitude

## Pre-Deployment Security Setup

### 1. Install Dependencies
```bash
cd backend
pip install slowapi==0.1.9
pip freeze > requirements.txt
```

### 2. Run Security Enhancement Scripts
```bash
# Add security features to main.py
python add_security_features.py

# Add rate limiting to auth endpoints
python add_auth_rate_limiting.py
```

### 3. Test Security Features Locally
```bash
# Start the server
uvicorn app.main:app --reload

# In another terminal, run security tests
python test_security.py

# Test rate limiting specifically
./test_rate_limiting.sh
```

### 4. Environment Variables for Production

Set these in Railway or your deployment platform:

```env
# Security (REQUIRED)
SECRET_KEY=<your-64-character-secure-key>  # Already set ✓
DEBUG=False
ENVIRONMENT=production

# Database (REQUIRED)
DATABASE_URL=<your-database-url>

# Optional but recommended
SENTRY_DSN=<your-sentry-dsn>  # For error monitoring
LOG_LEVEL=WARNING  # Reduce log verbosity in production
```

### 5. Verify Configuration Changes

The following changes should be in your `app/core/config.py`:

- ✅ `DEBUG: bool = Field(default=False)`
- ✅ `SECRET_KEY: str = Field(min_length=32)` (no default)
- ✅ `ALLOWED_HOSTS` restricted to specific domains
- ✅ Validation preventing DEBUG=True in production

### 6. Verify Security Middleware

Your `app/main.py` should now include:

- ✅ Security headers middleware
- ✅ Rate limiting setup
- ✅ Conditional API docs (disabled in production)

### 7. Verify Auth Endpoint Protection

Your `app/api/v1/endpoints/auth.py` should have:

- ✅ `@limiter.limit("5/minute")` on login
- ✅ `@limiter.limit("3/hour")` on register
- ✅ `@limiter.limit("10/hour")` on verify-email
- ✅ `@limiter.limit("3/hour")` on resend-verification

## Deployment Steps

1. **Commit all changes**
   ```bash
   git add .
   git commit -m "Add security enhancements: headers, rate limiting, production hardening"
   git push origin main
   ```

2. **Verify Railway environment variables**
   - Check SECRET_KEY is set (you mentioned it's already done ✓)
   - Add DEBUG=False
   - Add ENVIRONMENT=production

3. **Deploy and monitor**
   - Watch deployment logs for any errors
   - Once deployed, run security tests against production

## Post-Deployment Verification

Run security tests against your production URL:

```bash
# Test production security
python test_security.py --url https://talentprompt-production.up.railway.app

# Manual checks
# 1. Verify /docs returns 404
curl -I https://talentprompt-production.up.railway.app/docs

# 2. Check security headers
curl -I https://talentprompt-production.up.railway.app/api/v1/health

# 3. Test rate limiting
for i in {1..10}; do
  curl -X POST https://talentprompt-production.up.railway.app/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}'
done
```

## Security Monitoring

1. **Set up alerts for:**
   - Multiple failed login attempts
   - Rate limit violations
   - Unusual traffic patterns
   - 500 errors (potential security issues)

2. **Regular security tasks:**
   - Review logs weekly for suspicious activity
   - Update dependencies monthly
   - Rotate SECRET_KEY quarterly
   - Security audit semi-annually

## Quick Security Health Check

```bash
# Run this periodically to ensure security features are working
curl -s https://talentprompt-production.up.railway.app/api/v1/health | jq .

# Check security headers are present
curl -I https://talentprompt-production.up.railway.app/api/v1/health 2>/dev/null | grep -E "X-Content-Type-Options|X-Frame-Options|Strict-Transport-Security"
```

## Rollback Plan

If issues occur after deployment:

1. **Quick disable:** Set ENVIRONMENT=development temporarily
2. **Restore from backup:** 
   ```bash
   cp app/main.py.backup app/main.py
   cp app/api/v1/endpoints/auth.py.backup app/api/v1/endpoints/auth.py
   ```
3. **Redeploy previous version:** Use Railway's deployment history

## Additional Recommendations

1. **Enable Railway's DDoS protection** if available
2. **Set up Cloudflare** for additional security layer
3. **Configure database connection limits** to prevent connection exhaustion
4. **Implement request ID tracking** for better debugging
5. **Add application performance monitoring** (APM) tool

Remember: Security is an ongoing process, not a one-time setup!