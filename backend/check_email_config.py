#!/usr/bin/env python3
"""Check current email configuration in production."""

import requests
import json

def check_email_config():
    """Check email configuration via API."""
    # Production URL
    base_url = "https://promtitude-backend.up.railway.app"
    
    print("\n" + "="*60)
    print("CHECKING EMAIL CONFIGURATION")
    print("="*60)
    
    # Test the debug endpoint
    try:
        print(f"\n1. Testing email debug endpoint...")
        response = requests.get(f"{base_url}/test-email-debug")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {response.status_code}")
            print(f"   Email service type: {data.get('email_service_type', 'Unknown')}")
            print(f"   Email service module: {data.get('email_service_module', 'Unknown')}")
            print(f"   Mock email sent: {data.get('result', False)}")
            
            # Check if it's using SMTP or Mock
            if 'smtp' in data.get('email_service_module', '').lower():
                print("\n✅ SMTP email service is active!")
                print("   Real emails will be sent")
            else:
                print("\n⚠️  Mock email service is active")
                print("   Emails will only be logged, not sent")
        else:
            print(f"   Error: {response.status_code}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Prompt for real email test
    print("\n2. Would you like to test sending a real email?")
    email = input("   Enter your email address (or press Enter to skip): ").strip()
    
    if email and '@' in email:
        try:
            print(f"\n   Sending test email to {email}...")
            response = requests.post(
                f"{base_url}/api/v1/test-smtp-email",
                json={"email": email},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n   Results:")
                print(f"   - Email service: {data.get('email_service_type', 'Unknown')}")
                print(f"   - SMTP configured: {data.get('smtp_configured', False)}")
                print(f"   - SMTP host: {data.get('smtp_host', 'Not set')}")
                print(f"   - Test email sent: {data.get('test_sent', False)}")
                print(f"   - Invitation email sent: {data.get('invitation_sent', False)}")
                
                if data.get('errors'):
                    print(f"   - Errors: {', '.join(data['errors'])}")
                
                if data.get('test_sent'):
                    print("\n✅ Success! Check your email inbox (and spam folder)")
                    print("   You should receive:")
                    print("   1. A test configuration email")
                    print("   2. A sample invitation email")
                else:
                    print("\n❌ Email sending failed")
            else:
                print(f"   Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "="*60)
    print("EMAIL CHECK COMPLETE")
    print("="*60)

if __name__ == "__main__":
    check_email_config()