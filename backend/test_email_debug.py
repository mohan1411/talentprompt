#!/usr/bin/env python3
"""Test email service to debug console output."""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_email_service():
    """Test the email service directly."""
    print("\n" + "="*80)
    print("TESTING EMAIL SERVICE")
    print("="*80)
    
    # Import after path is set
    from app.services.email_service_production import get_email_service
    
    # Get email service
    print("\n1. Getting email service...")
    email_service = get_email_service()
    print(f"   Email service type: {type(email_service).__name__}")
    print(f"   Module: {email_service.__module__}")
    
    # Test sending an email
    print("\n2. Testing send_email method...")
    result = await email_service.send_email(
        to_email="test@example.com",
        subject="Test Email",
        html_content="<p>This is a test email</p>",
        text_content="This is a test email"
    )
    print(f"   Send result: {result}")
    
    # Test sending submission invitation
    print("\n3. Testing send_submission_invitation method...")
    result = await email_service.send_submission_invitation(
        to_email="candidate@example.com",
        candidate_name="John Doe",
        recruiter_name="Jane Smith",
        submission_link="http://localhost:3000/submit/test_token",
        message="Please submit your updated resume.",
        deadline_days=7,
        company_name="Test Company",
        is_update=True
    )
    print(f"   Send result: {result}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_email_service())