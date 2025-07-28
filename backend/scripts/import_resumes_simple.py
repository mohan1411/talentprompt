#!/usr/bin/env python3
"""Simple resume import script."""

import json
import os
from datetime import datetime
from uuid import uuid4
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.user import User
from app.models.resume import Resume

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://promtitude:promtitude123@localhost:5433/promtitude")

# Remove async driver if present
if "+asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")

print("="*60)
print("SIMPLE RESUME IMPORTER")
print("="*60)

# Create engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def import_resumes():
    """Import resumes from JSON file."""
    session = Session()
    
    try:
        # First, get the user
        email = "promtitude@gmail.com"
        user = session.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User {email} not found!")
            return
        
        print(f"✅ Found user: {email} (ID: {user.id})")
        
        # Check existing resumes
        existing_count = session.query(Resume).filter(Resume.user_id == user.id).count()
        print(f"   Existing resumes: {existing_count}")
        
        # Load the generated resumes
        json_file = "test_resumes_100.json"
        if not os.path.exists(json_file):
            print(f"\n❌ File not found: {json_file}")
            print("   Looking for test resume files...")
            # List available JSON files
            json_files = [f for f in os.listdir('.') if f.endswith('.json')]
            if json_files:
                print("   Available JSON files:")
                for f in json_files:
                    print(f"   - {f}")
            return
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON formats
        if isinstance(data, dict) and 'resumes' in data:
            test_resumes = data['resumes']
        elif isinstance(data, list):
            test_resumes = data
        else:
            print("❌ Unexpected JSON format")
            return
        
        print(f"\n📄 Found {len(test_resumes)} resumes to import")
        
        # Import each resume
        imported = 0
        for resume_data in test_resumes:
            try:
                # Create resume object
                resume = Resume(
                    id=uuid4(),
                    user_id=user.id,
                    first_name=resume_data['first_name'],
                    last_name=resume_data['last_name'],
                    email=resume_data.get('email', f"{resume_data['first_name'].lower()}.{resume_data['last_name'].lower()}@example.com"),
                    phone=resume_data.get('phone', '555-0100'),
                    location=resume_data.get('location', 'San Francisco, CA'),
                    summary=resume_data.get('summary', ''),
                    current_title=resume_data.get('current_title', 'Software Engineer'),
                    years_experience=resume_data.get('years_experience', 5),
                    skills=resume_data.get('skills', []),
                    raw_text=resume_data.get('summary', ''),  # Use summary as raw text
                    original_filename=f"{resume_data['first_name']}_{resume_data['last_name']}_resume.pdf",
                    file_size=1024 * 50,  # 50KB dummy size
                    file_type='application/pdf',
                    status='active',
                    parse_status='completed',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    parsed_at=datetime.utcnow(),
                    view_count=0,
                    search_appearance_count=0,
                    job_position=resume_data.get('current_title', 'Software Engineer')
                )
                
                session.add(resume)
                imported += 1
                
                if imported % 10 == 0:
                    print(f"   Imported {imported} resumes...")
                    
            except Exception as e:
                print(f"   ⚠️ Error importing {resume_data['first_name']} {resume_data['last_name']}: {e}")
                continue
        
        # Commit all changes
        session.commit()
        print(f"\n✅ Successfully imported {imported} resumes!")
        
        # Final count
        final_count = session.query(Resume).filter(Resume.user_id == user.id).count()
        print(f"   Total resumes for {email}: {final_count}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    import_resumes()
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("\n1. Open login_page.html in your browser")
    print("2. Click the login button")
    print("3. You should now see the imported resumes!")
    print("\nIf you still don't see resumes:")
    print("- Check the browser console for errors")
    print("- Make sure the frontend is running on http://localhost:3000")
    print("- Try refreshing the page after login")