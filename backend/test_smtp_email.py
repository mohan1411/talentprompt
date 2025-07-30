#!/usr/bin/env python3
"""Test SMTP email configuration."""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def test_smtp_configuration():
    """Test SMTP email sending."""
    print("\n" + "="*60)
    print("SMTP EMAIL CONFIGURATION TEST")
    print("="*60)
    
    # Import after environment is loaded
    from app.core.config import settings
    
    # Check configuration
    print("\n1. Checking SMTP configuration...")
    print(f"   SMTP_HOST: {settings.SMTP_HOST or 'Not set'}")
    print(f"   SMTP_PORT: {settings.SMTP_PORT}")
    print(f"   SMTP_USER: {settings.SMTP_USER or 'Not set'}")
    print(f"   SMTP_PASSWORD: {'Set' if settings.SMTP_PASSWORD else 'Not set'}")
    print(f"   SMTP_TLS: {settings.SMTP_TLS}")
    print(f"   FROM_EMAIL: {settings.EMAILS_FROM_EMAIL}")
    print(f"   FROM_NAME: {settings.EMAILS_FROM_NAME}")
    
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
        print("\n❌ SMTP configuration incomplete. Please set all required environment variables.")
        return
    
    # Get test email address
    test_email = input("\nEnter your email address to receive test email: ").strip()
    if not test_email or '@' not in test_email:
        print("❌ Invalid email address")
        return
    
    print(f"\n2. Testing email service...")
    print(f"   Sending test email to: {test_email}")
    
    try:
        # Import and test email service
        from app.services.email_service_smtp import EmailService
        email_service = EmailService()
        
        # Send test email
        result = await email_service.send_test_email(test_email)
        
        if result:
            print("\n✅ Test email sent successfully!")
            print(f"   Check your inbox at: {test_email}")
            print("   Note: It may take a few minutes to arrive")
            print("   Also check your spam folder")
        else:
            print("\n❌ Failed to send test email")
            print("   Check the console output above for error details")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nCommon issues:")
        print("- Wrong SMTP credentials")
        print("- Gmail: Need to use app password, not regular password")
        print("- SendGrid: Use 'apikey' as username and API key as password")
        print("- Firewall blocking SMTP ports")
    
    # Test submission invitation email
    print("\n3. Testing submission invitation email...")
    try:
        result = await email_service.send_submission_invitation(
            to_email=test_email,
            candidate_name="Test Candidate",
            recruiter_name="Jane Smith",
            submission_link="https://promtitude.com/submit/test_token_123",
            message="This is a test invitation to verify email formatting.",
            deadline_days=7,
            company_name="Test Company",
            is_update=False
        )
        
        if result:
            print("✅ Submission invitation email sent successfully!")
        else:
            print("❌ Failed to send submission invitation email")
            
    except Exception as e:
        print(f"❌ Error sending invitation: {e}")
    
    print("\n" + "="*60)
    print("EMAIL TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_smtp_configuration())