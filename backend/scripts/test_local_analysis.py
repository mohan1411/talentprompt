#!/usr/bin/env python3
"""Test query analysis locally to debug duplication."""

import requests
import json

# Test the local backend
print("Testing local query analysis...")

queries = ["Python", "python", "Python developer"]

# Get token from local storage or use a test token
token = input("Enter your local access token (from browser localStorage): ").strip()

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

for query in queries:
    print(f"\n{'='*60}")
    print(f"Testing query: '{query}'")
    print('='*60)
    
    # Test analyze-query endpoint
    url = f"http://localhost:8001/api/v1/search/analyze-query?query={query}"
    try:
        response = requests.post(url, headers=headers, json={})
        if response.status_code == 200:
            data = response.json()
            analysis = data.get('analysis', {})
            
            print("\nAnalysis response:")
            print(f"Primary skills: {analysis.get('primary_skills', [])}")
            print(f"Secondary skills: {analysis.get('secondary_skills', [])}")
            
            # Check for duplicates
            all_skills = analysis.get('primary_skills', []) + analysis.get('secondary_skills', [])
            skill_counts = {}
            for skill in all_skills:
                skill_lower = skill.lower()
                if skill_lower in skill_counts:
                    skill_counts[skill_lower].append(skill)
                else:
                    skill_counts[skill_lower] = [skill]
            
            duplicates = {k: v for k, v in skill_counts.items() if len(v) > 1}
            if duplicates:
                print(f"\n⚠️  DUPLICATES FOUND:")
                for skill_lower, occurrences in duplicates.items():
                    print(f"   '{skill_lower}' appears as: {occurrences}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")