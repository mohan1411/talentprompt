#!/usr/bin/env python3
"""Test the Pipeline API endpoints."""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
EMAIL = input("Enter your email: ")
PASSWORD = input("Enter your password: ")

def test_pipeline_api():
    print("\n🚀 Testing Pipeline API\n")
    
    # 1. Login
    print("1. Logging in...")
    login_data = {
        "username": EMAIL,
        "password": PASSWORD
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful!")
    
    # 2. Get default pipeline
    print("\n2. Getting default pipeline...")
    response = requests.get(f"{BASE_URL}/api/v1/workflow/default", headers=headers)
    
    if response.status_code == 200:
        pipeline = response.json()
        print(f"✅ Default pipeline: {pipeline['name']}")
        print(f"   ID: {pipeline['id']}")
        print(f"   Stages: {len(pipeline['stages'])}")
        for stage in pipeline['stages']:
            print(f"   - {stage['name']} ({stage['color']})")
        default_pipeline_id = pipeline['id']
    else:
        print(f"❌ Failed to get default pipeline: {response.text}")
        return
    
    # 3. List all pipelines
    print("\n3. Listing all pipelines...")
    response = requests.get(f"{BASE_URL}/api/v1/workflow/", headers=headers)
    
    if response.status_code == 200:
        pipelines = response.json()
        print(f"✅ Found {len(pipelines)} pipeline(s)")
    else:
        print(f"❌ Failed to list pipelines: {response.text}")
    
    # 4. Get your resumes to add to pipeline
    print("\n4. Getting your resumes...")
    response = requests.get(f"{BASE_URL}/api/v1/resumes/", headers=headers)
    
    if response.status_code == 200:
        resumes = response.json()
        print(f"✅ Found {len(resumes)} resume(s)")
        
        if resumes:
            # Add first resume to pipeline
            first_resume = resumes[0]
            print(f"\n5. Adding '{first_resume['first_name']} {first_resume['last_name']}' to pipeline...")
            
            add_data = {
                "candidate_id": first_resume['id'],
                "pipeline_id": default_pipeline_id
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/workflow/candidates/add",
                headers=headers,
                json=add_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Added to pipeline!")
                print(f"   Pipeline State ID: {result['pipeline_state_id']}")
                print(f"   Current Stage: {result['current_stage']}")
                
                # Add a note
                print(f"\n6. Adding a note...")
                note_data = {
                    "content": "Initial review - looks promising!",
                    "is_private": False
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/v1/workflow/candidates/{first_resume['id']}/notes",
                    headers=headers,
                    json=note_data
                )
                
                if response.status_code == 200:
                    print("✅ Note added successfully!")
                else:
                    print(f"❌ Failed to add note: {response.text}")
                    
            else:
                print(f"❌ Failed to add to pipeline: {response.text}")
        else:
            print("ℹ️  No resumes found. Upload a resume first to test pipeline features.")
    else:
        print(f"❌ Failed to get resumes: {response.text}")
    
    print("\n✨ Pipeline API test complete!")
    print("\nNext steps:")
    print("1. Upload some resumes if you haven't already")
    print("2. Try moving candidates through stages")
    print("3. Add evaluations after interviews")
    print("4. Check the candidate timeline")

if __name__ == "__main__":
    test_pipeline_api()