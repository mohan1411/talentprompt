#!/usr/bin/env python3
"""Test skills extraction from the Chrome extension perspective."""

import json

# Simulate Chrome extension data for Suhas
profile_data = {
    "linkedin_url": "https://www.linkedin.com/in/shudgur/",
    "name": "Suhas Shivakumar",
    "headline": "Continuous Improvement Manager at Ford Motor Company",
    "location": "Dearborn, Michigan, United States",
    "about": "Results-driven professional with expertise in Kaizen, lean manufacturing, and employee training.",
    "experience": [
        {
            "title": "Continuous Improvement Manager",
            "company": "Ford Motor Company",
            "duration": "Jan 2020 - Present",
            "description": "Leading Kaizen initiatives and strategy development"
        }
    ],
    "education": [],
    "skills": ["Kaizen", "Strategy", "Employee Training", "Project Management"],  # These are the expected skills
    "years_experience": 5,
    "email": "",
    "phone": ""
}

print("=== Chrome Extension Data ===")
print(f"Profile: {profile_data['name']}")
print(f"LinkedIn URL: {profile_data['linkedin_url']}")
print(f"Skills from extension: {profile_data['skills']}")
print(f"Number of skills: {len(profile_data['skills'])}")

# Check what happens during normalization
try:
    # Import the normalization function
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from app.services.search_skill_fix import normalize_skill_for_storage
    
    print("\n=== After Normalization ===")
    normalized_skills = [normalize_skill_for_storage(skill) for skill in profile_data['skills']]
    print(f"Normalized skills: {normalized_skills}")
    
    # Check if normalization changes anything
    for original, normalized in zip(profile_data['skills'], normalized_skills):
        if original != normalized:
            print(f"  Changed: '{original}' -> '{normalized}'")
        else:
            print(f"  Unchanged: '{original}'")
            
except ImportError as e:
    print(f"\nCouldn't import normalization function: {e}")
    print("Skills would be stored as-is from Chrome extension")

# Check how skills would be stored in JSON column
print("\n=== Database Storage ===")
print(f"Skills as JSON: {json.dumps(profile_data['skills'])}")
print(f"Type that would be stored: {type(profile_data['skills'])}")

# Check search patterns
print("\n=== Search Pattern Checks ===")
test_queries = ["Kaizen", "kaizen", "Employee Training", "employee training", "Strategy", "Project Management"]

for query in test_queries:
    # Check if query would match any skill
    matches = [skill for skill in profile_data['skills'] if query.lower() in skill.lower()]
    if matches:
        print(f"✓ Query '{query}' would match: {matches}")
    else:
        print(f"✗ Query '{query}' would NOT match any skills")

# Full text search
full_text = f"{profile_data['name']} {profile_data['headline']} {profile_data['about']} " + " ".join(profile_data['skills'])
print(f"\n=== Full Text Search ===")
print(f"Full text would contain all skills: {all(skill in full_text for skill in profile_data['skills'])}")

print("\n=== Debugging Tips ===")
print("1. Check if Suhas's profile exists in the database")
print("2. If it exists, check the 'skills' column - it should be a JSON array")
print("3. Check if skills are being extracted by the Chrome extension")
print("4. Check if skills are being normalized correctly on the backend")
print("5. Check the search conditions being generated for skill queries")