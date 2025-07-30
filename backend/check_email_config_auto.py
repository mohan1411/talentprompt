#!/usr/bin/env python3
"""Check current email configuration in production."""

import requests
import json
import sys

def check_email_config(test_email=None):
    """Check email configuration via API."""
    # Production URL
    base_url = "https://promtitude-backend.up.railway.app"
    
    print("\n" + "="*60)
    print("CHECKING EMAIL CONFIGURATION")
    print("="*60)
    
    # First check if API is accessible
    try:
        print(f"\n1. Testing API health...")
        response = requests.get(f"{base_url}/api/v1/health", timeout=10)
        print(f"   API Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ API is accessible")
        else:
            print("   ❌ API returned unexpected status")
    except Exception as e:
        print(f"   ❌ Cannot reach API: {e}")
        return
    
    # Test the debug endpoint
    try:
        print(f"\n2. Testing email debug endpoint...")
        response = requests.get(f"{base_url}/test-email-debug", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {response.status_code}")
            print(f"   Email service type: {data.get('email_service_type', 'Unknown')}")
            print(f"   Email service module: {data.get('email_service_module', 'Unknown')}")
            
            # Check if it's using SMTP or Mock
            if 'smtp' in data.get('email_service_module', '').lower():
                print("\n   ✅ SMTP email service is active!")
                print("   Real emails will be sent")
            else:
                print("\n   ⚠️  Mock email service is active")
                print("   Emails will only be logged, not sent")
        else:
            print(f"   Status: {response.status_code}")
            if response.status_code == 404:
                print("   Note: Debug endpoint not found (might need redeployment)")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test sending email if address provided
    if test_email:
        try:
            print(f"\n3. Sending test email to {test_email}...")
            response = requests.post(
                f"{base_url}/api/v1/test-smtp-email",
                json={"email": test_email},
                headers={"Content-Type": "application/json"},
                timeout=30
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
                    print("\n   ✅ Success! Check your email inbox (and spam folder)")
                    print("   You should receive:")
                    print("   1. A test configuration email")
                    print("   2. A sample invitation email")
                elif data.get('smtp_configured'):
                    print("\n   ⚠️  SMTP is configured but email sending failed")
                    print("   Check Railway logs for details")
                else:
                    print("\n   ℹ️  SMTP is not configured")
                    print("   Emails will be logged in console only")
            else:
                print(f"   Error: {response.status_code}")
                if response.status_code == 404:
                    print("   Note: Test endpoint not found (might need redeployment)")
                elif response.status_code == 422:
                    print("   Invalid request format")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "="*60)
    print("EMAIL CHECK COMPLETE")
    print("="*60)
    print("\nTo test with your email, run:")
    print(f"python3 {sys.argv[0]} your-email@example.com")

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else None
    check_email_config(email)