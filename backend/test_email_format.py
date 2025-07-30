#!/usr/bin/env python3
"""Test email formatting for candidate submissions."""

import asyncio
from datetime import datetime, timedelta

# Mock settings
class MockSettings:
    EMAILS_FROM_NAME = "Promtitude Team"
    EMAILS_FROM_EMAIL = "noreply@promtitude.com"
    FRONTEND_URL = "http://localhost:3000"

# Import with mocked settings
import sys
sys.path.insert(0, '.')
from app.services.email_service import EmailService

# Create service instance
email_service = EmailService()
email_service.template_env = None  # Skip template loading for test

async def test_emails():
    """Test email formatting."""
    
    print("\n" + "="*50 + " TESTING EMAIL FORMATS " + "="*50 + "\n")
    
    # Test 1: Update request from Resume page
    print("1. Testing UPDATE request email (from Resume page):")
    await email_service.send_email(
        to_email="michelle.garcia@example.com",
        subject="Request to Update Your Profile - Tech Corp",
        text_content="""Hi Michelle,

I hope this message finds you well. We'd like to ensure we have your most current information on file.

Would you mind taking a few minutes to update your profile with:
- Your current employment status and role
- Any new skills or certifications
- Your current location and availability
- Updated contact information

This helps us match you with the most relevant opportunities.

Please click the following link to update your information:
http://localhost:3000/submit/sub_dIfQN3gvhYyVPh5LWwnTTWcowY_LOA_mydkrUfK1Lhk

This link will expire in 7 days.

Best regards,
John Smith
Tech Corp""",
        html_content="<html><body>Email would be properly formatted in HTML</body></html>"
    )
    
    # Test 2: New submission request
    print("\n2. Testing NEW submission request email:")
    await email_service.send_email(
        to_email="mohan@example.com",
        subject="Invitation to Submit Your Profile - StartupX",
        text_content="""We're building a talent pool for exciting opportunities and would love to have your profile on file.

Would you be interested in submitting your resume and professional information? This will help us match you with relevant positions as they become available.

The process is quick and doesn't require creating an account.

Please click the following link to submit your information:
http://localhost:3000/submit/sub_rR5g4iMUsYRV07VmN18Y4UuiW6rnVqgQ0ro-JU538Ag

This link will expire in 7 days.

Best regards,
Sarah Johnson
StartupX""",
        html_content="<html><body>Email would be properly formatted in HTML</body></html>"
    )
    
    print("\n" + "="*50 + " TEST COMPLETE " + "="*50 + "\n")

if __name__ == "__main__":
    # Override settings
    import app.core.config
    app.core.config.settings = MockSettings()
    
    # Run test
    asyncio.run(test_emails())