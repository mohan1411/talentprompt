#!/usr/bin/env python3
"""Test AI-powered LinkedIn parser with sample data."""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.linkedin_parser import LinkedInParser


async def test_ai_parser():
    """Test the AI parser with sample LinkedIn data."""
    
    # Sample LinkedIn data based on user's profile
    sample_data = {
        "linkedin_url": "https://www.linkedin.com/in/sunil-narasimhappa/",
        "name": "Sunil Narasimhappa",
        "headline": "System Engineer",
        "location": "Stuttgart Region",
        "about": "",
        "experience": [],  # Empty from DOM extraction
        "education": [],   # Empty from DOM extraction
        "skills": ["Embedded Systems", "Automotive Engineering"],
        "full_text": """Sunil Narasimhappa
System Engineer
Stuttgart Region

EXPERIENCE

System Engineer at Valyue Consulting GmbH
Full-time
June 2023 - Present · 1 year 7 months
Stuttgart, Germany

Specialist at Robert Bosch Engineering and Business Solutions Ltd.
Full-time
September 2019 - May 2023 · 3 years 9 months
Bangalore, India
Working on automotive embedded systems development including software design, testing, and integration for various ECU modules.

EDUCATION

Bachelor of Engineering - BE, Electrical, Electronics and Communications Engineering
Kammavari Sangh Group & Institutions, BANGALORE SOUTH
2015 - 2019

SKILLS
Embedded Systems
Automotive Engineering
C Programming
AUTOSAR
CAN Protocol
Software Testing
System Integration
Requirements Engineering"""
    }
    
    # Initialize parser
    parser = LinkedInParser()
    
    print("Testing AI-powered LinkedIn parser...")
    print("-" * 50)
    
    # Test with AI
    if os.environ.get('OPENAI_API_KEY'):
        print("\n1. Testing WITH AI parsing:")
        ai_result = await parser.parse_linkedin_data(sample_data, use_ai=True)
        
        print(f"\nParsing method: {ai_result.get('parsing_method', 'unknown')}")
        print(f"Name: {ai_result.get('first_name')} {ai_result.get('last_name')}")
        print(f"Current Title: {ai_result.get('current_title')}")
        print(f"Location: {ai_result.get('location')}")
        print(f"Years of Experience: {ai_result.get('years_experience')}")
        print(f"Skills: {', '.join(ai_result.get('skills', []))}")
        print(f"Keywords: {', '.join(ai_result.get('keywords', []))}")
        
        print(f"\nExperience ({len(ai_result.get('experience', []))} entries):")
        for i, exp in enumerate(ai_result.get('experience', []), 1):
            print(f"  {i}. {exp.get('title')} at {exp.get('company')}")
            print(f"     Duration: {exp.get('duration')}")
            print(f"     Current: {exp.get('is_current', False)}")
            if exp.get('description'):
                print(f"     Description: {exp.get('description')[:100]}...")
        
        print(f"\nEducation ({len(ai_result.get('education', []))} entries):")
        for i, edu in enumerate(ai_result.get('education', []), 1):
            print(f"  {i}. {edu.get('degree')} in {edu.get('field')}")
            print(f"     School: {edu.get('school')}")
            print(f"     Dates: {edu.get('dates')}")
    else:
        print("\nWARNING: OPENAI_API_KEY not set. Cannot test AI parsing.")
        print("Set the environment variable to enable AI parsing:")
        print("export OPENAI_API_KEY='your-api-key'")
    
    print("\n" + "-" * 50)
    print("\n2. Testing WITHOUT AI (rule-based parsing):")
    rule_result = await parser.parse_linkedin_data(sample_data, use_ai=False)
    
    print(f"\nParsing method: rule-based")
    print(f"Name: {rule_result.get('first_name')} {rule_result.get('last_name')}")
    print(f"Years of Experience: {rule_result.get('years_experience')}")
    print(f"Experience entries: {len(rule_result.get('experience', []))}")
    print(f"Education entries: {len(rule_result.get('education', []))}")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(test_ai_parser())