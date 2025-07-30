#!/usr/bin/env python3
"""Test email configuration and sending."""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings
from app.services.email_service_production import get_email_service

# Get the email service instance
email_service = get_email_service()


async def test_email_config():
    """Test email configuration."""
    print("\n" + "="*50)
    print("EMAIL CONFIGURATION TEST")
    print("="*50)
    
    print(f"\nSMTP Host: {settings.SMTP_HOST or 'Not configured'}")
    print(f"SMTP Port: {settings.SMTP_PORT or 'Not configured'}")
    print(f"SMTP User: {settings.SMTP_USER or 'Not configured'}")
    print(f"SMTP Password: {'*' * len(settings.SMTP_PASSWORD) if settings.SMTP_PASSWORD else 'Not configured'}")
    print(f"From Email: {settings.EMAILS_FROM_EMAIL}")
    print(f"From Name: {settings.EMAILS_FROM_NAME}")
    
    if all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
        print("\n✅ SMTP is configured - will use real email sending")
    else:
        print("\n⚠️  SMTP not configured - will use mock email (console output)")
    
    print("\n" + "="*50)


async def send_test_email(to_email: str):
    """Send a test email."""
    print(f"\nSending test email to: {to_email}")
    
    try:
        subject = f"Promtitude Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2563eb;">Promtitude Email Test</h1>
                <p>This is a test email from your Promtitude application.</p>
                
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Configuration:</strong></p>
                    <ul style="margin: 5px 0;">
                        <li>SMTP Host: {settings.SMTP_HOST or 'Not configured'}</li>
                        <li>From: {settings.EMAILS_FROM_EMAIL}</li>
                        <li>Time: {datetime.now()}</li>
                    </ul>
                </div>
                
                <p>If you received this email, your email configuration is working correctly!</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280;">
                    <p>This is an automated test email from Promtitude.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Promtitude Email Test

This is a test email from your Promtitude application.

Configuration:
- SMTP Host: {settings.SMTP_HOST or 'Not configured'}
- From: {settings.EMAILS_FROM_EMAIL}
- Time: {datetime.now()}

If you received this email, your email configuration is working correctly!

This is an automated test email from Promtitude.
        """.strip()
        
        success = await email_service.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
        if success:
            print("✅ Email sent successfully!")
        else:
            print("❌ Email sending failed!")
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run email tests."""
    await test_email_config()
    
    if len(sys.argv) > 1:
        to_email = sys.argv[1]
        await send_test_email(to_email)
    else:
        print("\nUsage: python test_email.py <recipient-email>")
        print("Example: python test_email.py your-email@gmail.com")
        print("\nSkipping email send test - no recipient provided")


if __name__ == "__main__":
    print("Starting email test...")
    asyncio.run(main())