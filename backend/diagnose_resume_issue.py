#!/usr/bin/env python3
"""
Diagnose resume parsing/indexing issues in production.
Run this to understand why certain resumes are failing to index.
"""

import os
import sys
import requests
import json


def check_resume_issue(base_url="https://talentprompt-production.up.railway.app"):
    """Check for resume parsing issues via API."""
    
    print("🔍 Diagnosing Resume Indexing Issues")
    print("=" * 60)
    
    # The problematic resume ID from the error
    resume_id = "4772e109-7dd4-43b4-9c31-a36c0095fea2"
    
    print(f"\n📄 Checking resume: {resume_id}")
    print("This resume is failing with: 'user_id is required in metadata for security'")
    
    print("\n🔧 Possible causes:")
    print("1. Resume was created without a user_id (orphaned resume)")
    print("2. Resume upload process didn't properly set user_id")
    print("3. Bulk import process created resume without user association")
    print("4. Database migration issue left some resumes without user_id")
    
    print("\n📊 Diagnostic Steps:")
    print("1. Check database for resumes where user_id IS NULL")
    print("2. Verify bulk import process includes user_id")
    print("3. Add validation to prevent creating resumes without user_id")
    print("4. Run fix_resume_user_id.py script to repair orphaned resumes")
    
    print("\n🚀 Immediate Fix:")
    print("Run this in Railway shell or locally with production database:")
    print("```bash")
    print("python fix_resume_user_id.py 4772e109-7dd4-43b4-9c31-a36c0095fea2")
    print("```")
    
    print("\n🛡️ Prevention:")
    print("1. Add database constraint: ALTER TABLE resumes ALTER COLUMN user_id SET NOT NULL;")
    print("2. Add validation in Resume model to require user_id")
    print("3. Update bulk import to always include user_id")
    
    # Try to check via API if possible
    print("\n📡 Checking API health...")
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is accessible")
            
            # Check Qdrant health
            qdrant_response = requests.get(f"{base_url}/api/v1/health/qdrant", timeout=5)
            if qdrant_response.status_code == 200:
                data = qdrant_response.json()
                print(f"📊 Qdrant Status: {data.get('status', 'unknown')}")
                print(f"   Message: {data.get('message', '')}")
    except Exception as e:
        print(f"⚠️  Cannot reach API: {e}")
    
    print("\n" + "=" * 60)
    print("💡 Next Steps:")
    print("1. Connect to Railway shell")
    print("2. Run: python fix_resume_user_id.py")
    print("3. Monitor logs for any new occurrences")
    print("4. Consider adding the database constraint to prevent future issues")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://talentprompt-production.up.railway.app"
    
    check_resume_issue(base_url)