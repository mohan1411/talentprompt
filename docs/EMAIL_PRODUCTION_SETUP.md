# Email Production Setup Guide

## Overview

The application now supports both SMTP email sending for production and mock email for development. It automatically detects which to use based on environment configuration.

## Quick Setup

### 1. Gmail SMTP (Easiest for Testing)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and generate a password
   - Copy the 16-character password

3. **Set Environment Variables**:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
EMAILS_FROM_EMAIL=your-email@gmail.com
EMAILS_FROM_NAME=Promtitude Team
```

### 2. Custom Domain SMTP

For production, use your domain's SMTP server:

```bash
# Example for common providers
# Office 365
SMTP_HOST=smtp.office365.com
SMTP_PORT=587

# GoDaddy
SMTP_HOST=smtpout.secureserver.net
SMTP_PORT=465

# Your custom domain
SMTP_HOST=mail.yourdomain.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your-password
EMAILS_FROM_EMAIL=noreply@yourdomain.com
EMAILS_FROM_NAME=Promtitude Team
```

## Environment Configuration

### Development (.env)
```bash
# Leave SMTP settings empty to use mock email
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
```

### Production (.env.production)
```bash
# Configure all SMTP settings
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=promtitude@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=noreply@promtitude.com
EMAILS_FROM_NAME=Promtitude Team
```

## How It Works

1. **Automatic Detection**: The system checks if SMTP settings are configured
2. **SMTP Available**: Uses real email sending via SMTP
3. **SMTP Not Configured**: Falls back to mock email (prints to console)

## Testing Email

### 1. Local Testing with Real Email
```bash
# Set SMTP variables in .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=test@gmail.com
SMTP_PASSWORD=app-password

# Restart backend
cd backend
uvicorn app.main:app --reload

# Create a submission and check your email
```

### 2. Verify Email is Working
- Create a candidate submission invitation
- Check console logs for "Using SMTP email service"
- Verify email arrives in inbox

## Email Types Sent

1. **Submission Invitation** (to candidates)
   - Sent when recruiter invites candidate
   - Contains unique submission link
   - Shows expiration date

2. **Submission Confirmation** (to candidates)
   - Sent after successful submission
   - Confirms receipt of information

3. **Submission Notification** (to recruiters)
   - Sent when candidate submits
   - Links to resume in dashboard

## Production Checklist

- [ ] Configure SMTP settings in production environment
- [ ] Verify FROM email address matches your domain
- [ ] Test all email types before launch
- [ ] Set up SPF records for domain
- [ ] Monitor email delivery rates

## Troubleshooting

### Emails Not Sending
1. Check console logs for errors
2. Verify SMTP credentials
3. Check firewall allows SMTP port
4. Try telnet test: `telnet smtp.gmail.com 587`

### Gmail Specific Issues
- Use App Password, not regular password
- Enable "Less secure app access" (not recommended)
- Check Gmail sending limits (500/day)

### Deliverability Issues
- Emails going to spam? Check:
  - SPF records
  - FROM address matches domain
  - Email content not triggering spam filters

## Future Enhancements

1. **SendGrid Integration** (recommended for scale):
```python
# Future: sendgrid_service.py
import sendgrid
from sendgrid.helpers.mail import Mail

sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
```

2. **Email Analytics**:
- Track open rates
- Monitor delivery success
- A/B test templates

3. **Template Management**:
- Database-stored templates
- Admin UI for editing
- Version control for templates