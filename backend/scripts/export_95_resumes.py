#!/usr/bin/env python3
"""
Export the exact 95 active resumes for promtitude@gmail.com.
This will create a JSON file that can be imported to production.
"""

import psycopg2
import json
from datetime import datetime
import uuid

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, )):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

print("="*60)
print("EXPORTING 95 ACTIVE RESUMES")
print("="*60)

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="promtitude",
    user="promtitude",
    password="promtitude123"
)
cur = conn.cursor()

# First check what columns exist
print("\n1. Checking table structure...")
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'resumes'
    ORDER BY ordinal_position
""")
available_columns = [row[0] for row in cur.fetchall()]
print(f"   Found {len(available_columns)} columns in resumes table")

# Get the 95 active resumes with only existing columns
print("\n2. Fetching active resumes...")
cur.execute("""
    SELECT 
        r.id,
        r.first_name,
        r.last_name,
        r.email,
        r.phone,
        r.location,
        r.summary,
        r.skills,
        r.keywords,
        r.current_title,
        r.years_experience,
        r.job_position,
        r.raw_text,
        r.original_filename,
        r.file_size,
        r.file_type,
        r.linkedin_url,
        r.created_at,
        r.parsed_data,
        r.view_count,
        r.search_appearance_count
    FROM resumes r
    JOIN users u ON r.user_id = u.id
    WHERE u.email = 'promtitude@gmail.com'
    AND r.status != 'deleted'
    ORDER BY r.created_at DESC
""")

resumes = cur.fetchall()
print(f"   Found {len(resumes)} active resumes")

# Convert to list of dictionaries
resume_list = []
for row in resumes:
    resume = {
        "id": row[0],
        "first_name": row[1],
        "last_name": row[2],
        "email": row[3],
        "phone": row[4],
        "location": row[5],
        "summary": row[6],
        "skills": row[7] or [],
        "keywords": row[8] or [],
        "current_title": row[9],
        "years_experience": row[10],
        "job_position": row[11],
        "raw_text": row[12],
        "original_filename": row[13],
        "file_size": row[14],
        "file_type": row[15],
        "linkedin_url": row[16],
        "created_at": row[17],
        "parsed_data": row[18],
        "view_count": row[19],
        "search_appearance_count": row[20]
    }
    resume_list.append(resume)

cur.close()
conn.close()

# Save to JSON file
output_file = "promtitude_95_resumes_export.json"
print(f"\n3. Saving to {output_file}...")

export_data = {
    "export_date": datetime.now().isoformat(),
    "user_email": "promtitude@gmail.com",
    "resume_count": len(resume_list),
    "resumes": resume_list
}

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(export_data, f, indent=2, default=json_serial, ensure_ascii=False)

print(f"\n✅ Export complete!")
print(f"   File: {output_file}")
print(f"   Size: {len(json.dumps(export_data, default=json_serial)) / 1024 / 1024:.2f} MB")
print(f"   Resumes: {len(resume_list)}")

# Create a summary
print("\n4. Resume Summary:")
print("   Sample resumes included:")
for i, resume in enumerate(resume_list[:5]):
    print(f"   - {resume['first_name']} {resume['last_name']} ({resume['current_title'] or 'No title'})")
print(f"   ... and {len(resume_list) - 5} more")

# Calculate statistics
skills_count = sum(len(r['skills'] or []) for r in resume_list)
avg_experience = sum(r['years_experience'] or 0 for r in resume_list) / len(resume_list)

print(f"\n   Statistics:")
print(f"   - Total unique skills: {len(set(skill for r in resume_list for skill in (r['skills'] or [])))}")
print(f"   - Average years experience: {avg_experience:.1f}")
print(f"   - Resumes with LinkedIn: {sum(1 for r in resume_list if r['linkedin_url'])}")

print("\n📋 Next steps:")
print("1. Copy 'promtitude_95_resumes_export.json' to your production environment")
print("2. Run the import script on production")
print("3. Verify the import was successful")