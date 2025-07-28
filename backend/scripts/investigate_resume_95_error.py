#!/usr/bin/env python3
"""Investigate the specific issue with resume at position 95+."""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime
from uuid import UUID

# Custom JSON encoder for database results
class DatabaseEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        return super().default(obj)

async def main():
    print("="*60)
    print("INVESTIGATING RESUME POSITION 95+ ERROR")
    print("="*60)
    
    # Use async connection
    DATABASE_URL = "postgresql+asyncpg://promtitude:promtitude123@localhost:5433/promtitude"
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # First, get the exact resume at position 95 (0-indexed, so 96th resume)
        print("\n1. Finding resume at position 95 (96th resume)...")
        
        result = await session.execute(text("""
            WITH ordered_resumes AS (
                SELECT 
                    r.*,
                    row_number() OVER (ORDER BY r.created_at DESC) - 1 as position
                FROM resumes r
                JOIN users u ON r.user_id = u.id
                WHERE u.email = 'promtitude@gmail.com'
                AND r.status != 'deleted'
            )
            SELECT 
                position,
                id,
                first_name,
                last_name,
                email,
                phone,
                location,
                status,
                parse_status,
                original_filename,
                file_hash,
                years_experience,
                current_title,
                job_position,
                linkedin_url,
                github_url,
                portfolio_url,
                created_at,
                updated_at,
                parsed_at,
                view_count,
                LENGTH(raw_text) as raw_text_length,
                LENGTH(summary) as summary_length,
                LENGTH(achievements::text) as achievements_length,
                LENGTH(certifications::text) as certifications_length,
                LENGTH(languages::text) as languages_length,
                skills IS NULL as skills_null,
                array_length(skills, 1) as skills_count,
                education IS NULL as education_null,
                experience IS NULL as experience_null
            FROM ordered_resumes
            WHERE position BETWEEN 90 AND 100
            ORDER BY position
        """))
        
        rows = result.fetchall()
        print(f"\nFound {len(rows)} resumes around position 95")
        
        problematic_resume = None
        print("\nPos | Name                     | Status | Parse    | Skills | Education | Experience")
        print("-"*85)
        
        for row in rows:
            pos = row[0]
            id = row[1]
            fname = row[2] or "NULL"
            lname = row[3] or "NULL"
            status = row[7]
            parse_status = row[8]
            skills_null = row[27]
            skills_count = row[28]
            edu_null = row[29]
            exp_null = row[30]
            
            marker = " <-- ERROR STARTS HERE" if pos == 95 else ""
            print(f"{pos:3d} | {fname[:15]:15s} {lname[:8]:8s} | {status:6s} | {parse_status:8s} | {'NULL' if skills_null else str(skills_count or 0):6s} | {'NULL' if edu_null else 'OK':9s} | {'NULL' if exp_null else 'OK':10s}{marker}")
            
            if pos == 95:
                problematic_resume = row
        
        if problematic_resume:
            print(f"\n2. Detailed analysis of resume at position 95:")
            print(f"   ID: {problematic_resume[1]}")
            print(f"   Name: {problematic_resume[2]} {problematic_resume[3]}")
            print(f"   Email: {problematic_resume[4]}")
            print(f"   Status: {problematic_resume[7]}")
            print(f"   Parse Status: {problematic_resume[8]}")
            print(f"   Raw Text Length: {problematic_resume[21]}")
            print(f"   Summary Length: {problematic_resume[22]}")
            
            # Check for potential serialization issues
            resume_id = problematic_resume[1]
            
            # Get the full resume data
            print(f"\n3. Checking for data issues in resume {resume_id}...")
            
            result = await session.execute(text("""
                SELECT 
                    r.skills,
                    r.education::text,
                    r.experience::text,
                    r.achievements,
                    r.certifications,
                    r.languages
                FROM resumes r
                WHERE r.id = :resume_id
            """), {"resume_id": resume_id})
            
            data_row = result.fetchone()
            if data_row:
                skills, education, experience, achievements, certifications, languages = data_row
                
                print("\n   Data field checks:")
                print(f"   - Skills: {type(skills).__name__} - {'NULL' if skills is None else f'{len(skills)} items'}")
                print(f"   - Education: {'NULL' if education is None else f'{len(education)} chars'}")
                print(f"   - Experience: {'NULL' if experience is None else f'{len(experience)} chars'}")
                print(f"   - Achievements: {type(achievements).__name__} - {'NULL' if achievements is None else 'Present'}")
                print(f"   - Certifications: {type(certifications).__name__} - {'NULL' if certifications is None else 'Present'}")
                print(f"   - Languages: {type(languages).__name__} - {'NULL' if languages is None else 'Present'}")
                
                # Try to serialize the problematic fields
                print("\n4. Testing JSON serialization...")
                try:
                    test_data = {
                        "skills": skills,
                        "achievements": achievements,
                        "certifications": certifications,
                        "languages": languages
                    }
                    json_str = json.dumps(test_data, cls=DatabaseEncoder)
                    print("   ✅ Basic fields serialize OK")
                except Exception as e:
                    print(f"   ❌ Serialization error: {e}")
                
                # Check if education/experience can be parsed
                if education:
                    try:
                        edu_data = json.loads(education)
                        print(f"   ✅ Education JSON is valid ({len(edu_data)} entries)")
                    except Exception as e:
                        print(f"   ❌ Education JSON is invalid: {e}")
                        print(f"      First 200 chars: {education[:200]}")
                
                if experience:
                    try:
                        exp_data = json.loads(experience)
                        print(f"   ✅ Experience JSON is valid ({len(exp_data)} entries)")
                    except Exception as e:
                        print(f"   ❌ Experience JSON is invalid: {e}")
                        print(f"      First 200 chars: {experience[:200]}")
        
        # Check for common data issues across all resumes
        print("\n5. Checking for common issues across all resumes...")
        
        result = await session.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN skills IS NULL THEN 1 END) as null_skills,
                COUNT(CASE WHEN education IS NULL THEN 1 END) as null_education,
                COUNT(CASE WHEN experience IS NULL THEN 1 END) as null_experience,
                COUNT(CASE WHEN raw_text IS NULL THEN 1 END) as null_raw_text,
                COUNT(CASE WHEN summary IS NULL THEN 1 END) as null_summary
            FROM resumes r
            JOIN users u ON r.user_id = u.id
            WHERE u.email = 'promtitude@gmail.com'
            AND r.status != 'deleted'
        """))
        
        stats = result.fetchone()
        if stats:
            total, null_skills, null_edu, null_exp, null_text, null_summary = stats
            print(f"   Total resumes: {total}")
            print(f"   Null skills: {null_skills}")
            print(f"   Null education: {null_edu}")
            print(f"   Null experience: {null_exp}")
            print(f"   Null raw_text: {null_text}")
            print(f"   Null summary: {null_summary}")
        
        # Test direct API query simulation
        print("\n6. Simulating API query...")
        
        # This simulates what the API does
        result = await session.execute(text("""
            SELECT 
                r.id,
                r.first_name,
                r.last_name,
                r.email,
                r.phone,
                r.skills,
                r.years_experience,
                r.current_title,
                r.location,
                r.summary,
                r.status,
                r.parse_status,
                r.job_position,
                r.created_at,
                r.updated_at,
                r.view_count
            FROM resumes r
            JOIN users u ON r.user_id = u.id
            WHERE u.email = 'promtitude@gmail.com'
            AND r.status != 'deleted'
            ORDER BY r.created_at DESC
            LIMIT 10 OFFSET 95
        """))
        
        try:
            api_rows = result.fetchall()
            print(f"   ✅ Query returned {len(api_rows)} rows")
            
            # Try to convert to dict like API does
            for i, row in enumerate(api_rows):
                try:
                    resume_dict = {
                        "id": str(row[0]),
                        "first_name": row[1],
                        "last_name": row[2],
                        "email": row[3],
                        "phone": row[4],
                        "skills": row[5],
                        "years_experience": row[6],
                        "current_title": row[7],
                        "location": row[8],
                        "summary": row[9],
                        "status": row[10],
                        "parse_status": row[11],
                        "job_position": row[12],
                        "created_at": row[13].isoformat() if row[13] else None,
                        "updated_at": row[14].isoformat() if row[14] else None,
                        "view_count": row[15]
                    }
                    # This would fail if there's a serialization issue
                    json.dumps(resume_dict, cls=DatabaseEncoder)
                    print(f"   ✅ Resume {i} at position {95+i} serializes OK")
                except Exception as e:
                    print(f"   ❌ Resume {i} at position {95+i} fails: {e}")
                    print(f"      Name: {row[1]} {row[2]}")
                    print(f"      ID: {row[0]}")
        except Exception as e:
            print(f"   ❌ Query failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())