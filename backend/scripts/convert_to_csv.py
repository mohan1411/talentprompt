#!/usr/bin/env python3
"""Convert test resumes JSON to CSV for easy upload."""

import json
import csv
import os

def json_to_csv():
    """Convert test_resumes_100.json to CSV format."""
    
    # Load JSON
    with open('test_resumes_100.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    resumes = data['resumes']
    
    # Create CSV
    with open('test_resumes_100.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'first_name', 'last_name', 'email', 'phone', 'location',
            'current_title', 'years_experience', 'skills', 'summary'
        ])
        
        # Data rows
        for resume in resumes:
            writer.writerow([
                resume['first_name'],
                resume['last_name'],
                resume['email'],
                resume.get('phone', ''),
                resume.get('location', ''),
                resume.get('current_title', ''),
                resume.get('years_experience', ''),
                '|'.join(resume.get('skills', [])),  # Skills separated by |
                resume.get('summary', '')
            ])
    
    print("✅ Created test_resumes_100.csv")
    print("   This file can be imported via UI bulk upload")

if __name__ == "__main__":
    json_to_csv()