# Email Setup Guide for Promtitude

## Quick Start with Gmail (Free)

### Step 1: Enable 2-Factor Authentication
1. Go to https://myaccount.google.com/security
2. Click on "2-Step Verification" 
3. Follow the setup process

### Step 2: Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" from the dropdown
3. Select "Other" and enter "Promtitude"
4. Click "Generate"
5. **Copy the 16-character password** (you won't see it again!)

### Step 3: Configure Backend Environment

Add these to your backend `.env` file:

```bash
# Email Configuration
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # The 16-character app password (no spaces)
EMAILS_FROM_EMAIL=your-email@gmail.com
EMAILS_FROM_NAME=Promtitude
```

### Step 4: Deploy to Production

Add the same environment variables to Railway:
1. Go to your Railway project
2. Click on the backend service
3. Go to "Variables" tab
4. Add each email configuration variable

## Testing Email Verification

1. Register a new account on your site
2. Check your email for the verification message
3. Check spam folder if not in inbox
4. The email will show as sent from your Gmail address

## Gmail Limits
- **Daily limit**: 500 emails/day
- **Rate limit**: 20 emails/minute
- Perfect for MVP stage!

## Future Upgrade Options

### When you reach 100+ users:
**SendGrid Free Tier**
- 100 emails/day forever free
- Better deliverability
- Professional sender reputation
- Sign up at: https://sendgrid.com/free/

### When you have revenue:
**Custom Domain Email** (noreply@promtitude.com)
1. Google Workspace: $6/month
2. Or use SendGrid with domain authentication

### For scale (1000+ users):
**AWS SES**
- $0.10 per 1000 emails
- Extremely reliable
- Used by major companies

## Troubleshooting

### Emails going to spam?
1. Ask users to check spam folder
2. Tell them to mark as "Not Spam"
3. Consider upgrading to SendGrid

### App password not working?
1. Make sure 2FA is enabled
2. Remove spaces from the password
3. Check if "Less secure app access" is needed (usually not)

### Not receiving emails?
1. Check Railway logs for errors
2. Verify all SMTP settings are correct
3. Test with a different email address

## Security Note
- Never commit your app password to Git
- Use environment variables only
- Rotate app password periodically
- Consider using a dedicated email account for the app