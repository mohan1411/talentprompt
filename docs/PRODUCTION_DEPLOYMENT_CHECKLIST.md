# Production Deployment Checklist

## 🚀 Phase 1 Deployed Successfully!

Commit: `e048c9d` - feat: Implement Phase 1 candidate submission system

## Backend Deployment Steps

### 1. Database Migration
Run the new migration on your production database:
```bash
cd backend
alembic upgrade head
```

### 2. Environment Variables
Add these to your production environment (Railway/Heroku/etc):

#### Required (Already Set):
- All existing database and API keys should work

#### Optional Email Configuration:
If you want real emails in production, add:
```bash
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-production-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
EMAILS_FROM_EMAIL=noreply@promtitude.com
EMAILS_FROM_NAME=Promtitude Team
```

Without these, the system will use mock emails (prints to logs).

### 3. Verify Deployment
After deployment, check:
- [ ] Backend logs show "Application startup complete"
- [ ] Database migration completed successfully
- [ ] API endpoint works: `GET /api/v1/submissions/health`

## Frontend Deployment Steps

### 1. Environment Variables
Ensure these are set in Vercel:
- `NEXT_PUBLIC_API_URL` - Your backend URL

### 2. Deploy to Vercel
The push to main should trigger automatic deployment.

### 3. Verify Frontend
- [ ] Submission page loads: `/submit/test-token` (will show error for invalid token)
- [ ] Dashboard shows "Invite New Candidate" button
- [ ] Resume cards show "Request Update" button

## Testing in Production

### 1. Test Without Real Emails (Default)
1. Go to Dashboard > Resumes
2. Click "Request Update" on any resume
3. Check backend logs for email content
4. Copy the submission link from logs
5. Test the submission flow

### 2. Test With Real Emails (If Configured)
1. Add SMTP settings to production environment
2. Restart backend service
3. Create a test invitation
4. Check your email inbox

## Feature Summary

✅ **What's New:**
- Recruiters can request profile updates from candidates
- Candidates submit without creating accounts
- Automatic email notifications
- Duplicate resume prevention
- Update timestamps on resumes

## Monitoring

Watch for:
- Backend logs for any errors
- Database connection issues
- Email sending failures (if SMTP configured)

## Rollback Plan

If issues occur:
```bash
# Revert to previous commit
git revert e048c9d
git push origin main

# Or checkout previous version
git checkout f4da890
git push --force origin main
```

## Next Steps

1. Monitor error logs for first 24 hours
2. Test complete flow with a real candidate
3. Gather feedback from users
4. Plan Phase 2 features

## Support

If you encounter issues:
1. Check backend logs first
2. Verify all environment variables
3. Ensure database migration completed
4. Test API endpoints directly

The system is designed to fail gracefully - if emails don't work, it will still function with console logging.