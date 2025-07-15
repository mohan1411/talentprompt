#!/bin/bash

# Test if AI parsing is working on the backend

echo "Testing Backend AI Configuration..."
echo "=================================="

# First, login to get auth token
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST https://talentprompt-production.up.railway.app/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$TOKEN" ]; then
  echo "Failed to login. Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✓ Login successful"

# Test LinkedIn import with sample data
echo -e "\n2. Testing LinkedIn import with AI parsing..."

PROFILE_DATA='{
  "linkedin_url": "https://www.linkedin.com/in/test-profile/",
  "name": "Test User",
  "headline": "System Engineer",
  "location": "Stuttgart Region",
  "experience": [],
  "skills": ["Embedded Systems", "Automotive Engineering"],
  "years_experience": 0,
  "full_text": "Test User\nSystem Engineer\nStuttgart Region\n18 years of experience\n\nEXPERIENCE\n\nSystem Engineer\nValyue Consulting GmbH\nJan 2014 - Present · 11 yrs 7 mos\nStuttgart, Germany\n\nSpecialist\nRobert Bosch Engineering and Business Solutions Ltd.\nJun 2007 - Aug 2013 · 6 yrs 3 mos\nBangalore, India\n\nSKILLS\nEmbedded Systems, Automotive Engineering"
}'

IMPORT_RESPONSE=$(curl -s -X POST https://talentprompt-production.up.railway.app/api/v1/linkedin/import-profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PROFILE_DATA")

echo "Import response: $IMPORT_RESPONSE"

# Check if it calculated years of experience
if echo "$IMPORT_RESPONSE" | grep -q "success.*true"; then
  echo "✓ Import successful"
  
  # Extract candidate_id
  CANDIDATE_ID=$(echo $IMPORT_RESPONSE | grep -o '"candidate_id":"[^"]*' | sed 's/"candidate_id":"//')
  
  if [ ! -z "$CANDIDATE_ID" ]; then
    echo -e "\n3. Fetching imported profile..."
    PROFILE_RESPONSE=$(curl -s -X GET "https://talentprompt-production.up.railway.app/api/v1/resumes/$CANDIDATE_ID" \
      -H "Authorization: Bearer $TOKEN")
    
    echo "Profile data:"
    echo "$PROFILE_RESPONSE" | python3 -m json.tool | grep -E "(years_experience|first_name|last_name|parsed_data)"
  fi
else
  echo "✗ Import failed"
fi