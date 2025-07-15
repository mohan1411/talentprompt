#!/usr/bin/env python3
"""Test script for LinkedIn integration."""

import asyncio
import json
from datetime import datetime

# Mock LinkedIn profile data
mock_profile_data = {
    "linkedin_url": "https://www.linkedin.com/in/johndoe",
    "name": "John Doe",
    "headline": "Senior Python Developer | Full Stack Engineer | AWS Certified",
    "location": "San Francisco, CA",
    "about": """Experienced software engineer with 8+ years building scalable web applications.
    Expertise in Python, Django, React, and cloud technologies.
    Passionate about clean code and mentoring junior developers.""",
    "experience": [
        {
            "title": "Senior Software Engineer",
            "company": "Tech Corp",
            "location": "San Francisco, CA",
            "duration": "Jan 2020 - Present · 4 years",
            "description": "Leading backend development for microservices architecture"
        },
        {
            "title": "Software Engineer",
            "company": "StartupXYZ",
            "location": "San Francisco, CA",
            "duration": "Jun 2017 - Dec 2019 · 2 years 7 months",
            "description": "Full stack development using Python and React"
        },
        {
            "title": "Junior Developer",
            "company": "WebDev Inc",
            "location": "San Jose, CA",
            "duration": "Aug 2015 - May 2017 · 1 year 10 months",
            "description": "Frontend development and API integration"
        }
    ],
    "education": [
        {
            "school": "University of California, Berkeley",
            "degree": "Bachelor of Science",
            "field": "Computer Science",
            "year": "2011 - 2015"
        }
    ],
    "skills": [
        "Python", "Django", "FastAPI", "React", "JavaScript",
        "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS",
        "Git", "CI/CD", "Agile", "TDD", "REST APIs"
    ]
}

async def test_linkedin_parser():
    """Test the LinkedIn parser service."""
    from app.services.linkedin_parser import LinkedInParser
    
    parser = LinkedInParser()
    parsed_data = await parser.parse_linkedin_data(mock_profile_data)
    
    print("=== LinkedIn Parser Test Results ===")
    print(f"Name: {parsed_data['first_name']} {parsed_data['last_name']}")
    print(f"Years of Experience: {parsed_data['years_experience']}")
    print(f"Keywords: {', '.join(parsed_data['keywords'][:10])}")
    print(f"Experience entries: {len(parsed_data['experience'])}")
    print(f"Education entries: {len(parsed_data['education'])}")
    print(f"Raw text length: {len(parsed_data['raw_text'])} characters")
    
    # Print experience details
    print("\n=== Experience ===")
    for exp in parsed_data['experience']:
        print(f"- {exp['title']} at {exp['company']} ({exp['duration']})")
        if exp['is_current']:
            print("  [CURRENT POSITION]")
    
    # Print education details
    print("\n=== Education ===")
    for edu in parsed_data['education']:
        print(f"- {edu['degree']} in {edu['field']} from {edu['school']} ({edu['year']})")
    
    return parsed_data

def test_chrome_extension_data():
    """Test Chrome extension data format."""
    print("\n=== Chrome Extension Data Format ===")
    print("Expected format for Chrome extension to send:")
    print(json.dumps(mock_profile_data, indent=2))

if __name__ == "__main__":
    print("Testing LinkedIn Integration Components\n")
    
    # Test parser
    asyncio.run(test_linkedin_parser())
    
    # Show Chrome extension format
    test_chrome_extension_data()
    
    print("\n✅ LinkedIn integration components are ready!")
    print("\nNext steps:")
    print("1. Run database migration: alembic upgrade head")
    print("2. Load the Chrome extension in Chrome (chrome://extensions/)")
    print("3. Navigate to a LinkedIn profile")
    print("4. Click the TalentPrompt extension icon")
    print("5. Import the profile to test the full flow")