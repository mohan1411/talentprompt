# Brevo Email Setup Guide for Promtitude

This guide will help you set up Brevo (formerly Sendinblue) for sending emails from Promtitude.

## Why Brevo?

- **Free tier**: 300 emails/day free forever
- **Affordable**: Much cheaper than SendGrid for small volumes
- **Easy setup**: Simple SMTP configuration
- **Good deliverability**: Established email infrastructure
- **No credit card required** for free tier

## Step 1: Create Brevo Account

1. Go to [https://www.brevo.com](https://www.brevo.com)
2. Click "Sign up free"
3. Complete the registration process
4. Verify your email address

## Step 2: Configure Sender Domain (Recommended)

For better deliverability, authenticate your domain:

1. In Brevo dashboard, go to **Settings** > **Senders & IP**
2. Click **Domains** tab
3. Click **Add a domain**
4. Enter `promtitude.com` (or your domain)
5. Follow the instructions to add DNS records:
   - SPF record
   - DKIM records
   - DMARC record (optional but recommended)

## Step 3: Create SMTP Key

1. Go to **SMTP & API** in the left sidebar
2. Click **SMTP settings** tab
3. Click **Generate a new SMTP key**
4. Give it a name like "Promtitude Production"
5. Copy the generated key (you won't see it again!)

## Step 4: Configure Railway Environment Variables

Add these environment variables in Railway:

```bash
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp-relay.brevo.com
SMTP_USER=your-login-email@example.com
SMTP_PASSWORD=your-smtp-key-from-step-3
EMAILS_FROM_EMAIL=noreply@promtitude.com
EMAILS_FROM_NAME=Promtitude Team
```

**Important Notes:**
- `SMTP_USER` must be the email you used to sign up for Brevo
- `SMTP_PASSWORD` is the SMTP key, NOT your Brevo account password
- `EMAILS_FROM_EMAIL` should ideally use your authenticated domain

## Step 5: Test Configuration

### Option A: Using the API endpoint
```bash
curl -X POST https://promtitude-backend.up.railway.app/api/v1/test-smtp-email \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com"}'
```

### Option B: Test locally first
```bash
# In your .env file
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp-relay.brevo.com
SMTP_USER=your-brevo-email@example.com
SMTP_PASSWORD=your-brevo-smtp-key

# Run test
cd backend
python3 test_smtp_email.py
```

## Step 6: Monitor Email Activity

1. In Brevo dashboard, go to **Transactional** > **Email Activity**
2. You'll see all sent emails, opens, clicks, etc.
3. Check for any bounces or blocks

## Troubleshooting

### Common Issues:

1. **Authentication failed**
   - Make sure you're using the SMTP key, not your account password
   - Verify the email in SMTP_USER matches your Brevo account

2. **Emails going to spam**
   - Complete domain authentication (Step 2)
   - Ensure FROM address matches authenticated domain
   - Avoid spam trigger words in subject/content

3. **Rate limit exceeded**
   - Free tier: 300 emails/day
   - Upgrade to paid plan for higher limits

4. **Connection timeout**
   - Check if Railway allows outbound SMTP (it should)
   - Try port 2525 if 587 is blocked

### Brevo SMTP Settings Summary:
- **Server**: smtp-relay.brevo.com
- **Port**: 587 (or 2525 as fallback)
- **Security**: TLS
- **Username**: Your Brevo account email
- **Password**: Your SMTP key (not account password)

## Email Templates

Brevo also offers:
- Transactional email templates (optional)
- Email tracking and analytics
- Webhook notifications for email events

For now, we're using SMTP which sends our custom HTML templates directly.

## Support

- Brevo Documentation: https://developers.brevo.com/docs
- SMTP Guide: https://developers.brevo.com/docs/smtp-relay
- Support: support@brevo.com