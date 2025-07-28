#!/usr/bin/env python3
"""
Debug the backend error at position 95.

Run this script from the backend directory:
cd /mnt/d/Projects/AI/BusinessIdeas/SmallBusiness/TalentPrompt/backend
python scripts/debug_backend_error.py
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import Resume as ResumeSchema
from pydantic import ValidationError
import json
from datetime import datetime
from uuid import UUID

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Custom JSON encoder
class DatabaseEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

async def main():
    print("="*60)
    print("DEBUGGING BACKEND ERROR AT POSITION 95")
    print("="*60)
    
    # Database connection
    DATABASE_URL = "postgresql+asyncpg://promtitude:promtitude123@localhost:5433/promtitude"
    engine = create_async_engine(DATABASE_URL, echo=True)  # Echo SQL for debugging
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get the user
        result = await db.execute(
            select(User).where(User.email == "promtitude@gmail.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User not found!")
            return
        
        print(f"✅ Found user: {user.email} (ID: {user.id})")
        
        # Simulate the exact query used by the API
        print("\n1. Testing API query with skip=95, limit=10...")
        try:
            result = await db.execute(
                select(Resume)
                .where(Resume.user_id == user.id)
                .where(Resume.status != 'deleted')
                .order_by(Resume.created_at.desc())
                .offset(95)
                .limit(10)
            )
            resumes = result.scalars().all()
            print(f"   ✅ Query returned {len(resumes)} resumes")
            
            # Try to serialize each resume
            for i, resume in enumerate(resumes):
                try:
                    # Convert to schema (this is what the API does)
                    resume_schema = ResumeSchema.model_validate(resume)
                    # Try to convert to JSON
                    json_data = resume_schema.model_dump_json()
                    print(f"   ✅ Resume {i} (pos {95+i}): {resume.first_name} {resume.last_name} - OK")
                except ValidationError as e:
                    print(f"   ❌ Resume {i} (pos {95+i}): Validation error - {e}")
                    print(f"      ID: {resume.id}")
                    print(f"      Name: {resume.first_name} {resume.last_name}")
                    
                    # Check specific fields
                    print("      Field checks:")
                    for field in ['skills', 'education', 'experience', 'achievements', 'certifications', 'languages']:
                        value = getattr(resume, field, None)
                        if value is not None:
                            print(f"        - {field}: {type(value).__name__}")
                            if hasattr(value, '__len__'):
                                print(f"          Length: {len(value)}")
                except Exception as e:
                    print(f"   ❌ Resume {i} (pos {95+i}): Error - {type(e).__name__}: {e}")
                    print(f"      ID: {resume.id}")
                    print(f"      Name: {resume.first_name} {resume.last_name}")
                    
        except Exception as e:
            print(f"   ❌ Query failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        
        # Test individual positions
        print("\n2. Testing individual positions around 95...")
        for pos in [93, 94, 95, 96, 97]:
            try:
                result = await db.execute(
                    select(Resume)
                    .where(Resume.user_id == user.id)
                    .where(Resume.status != 'deleted')
                    .order_by(Resume.created_at.desc())
                    .offset(pos)
                    .limit(1)
                )
                resume = result.scalar_one_or_none()
                
                if resume:
                    try:
                        # Try to validate with schema
                        resume_schema = ResumeSchema.model_validate(resume)
                        json_data = resume_schema.model_dump_json()
                        print(f"   Position {pos}: ✅ {resume.first_name} {resume.last_name}")
                    except Exception as e:
                        print(f"   Position {pos}: ❌ {resume.first_name} {resume.last_name} - {type(e).__name__}")
                        
                        # Debug the specific resume
                        print(f"     Debugging resume at position {pos}:")
                        print(f"     - ID: {resume.id}")
                        print(f"     - Skills type: {type(resume.skills).__name__ if resume.skills else 'None'}")
                        print(f"     - Education type: {type(resume.education).__name__ if resume.education else 'None'}")
                        print(f"     - Experience type: {type(resume.experience).__name__ if resume.experience else 'None'}")
                else:
                    print(f"   Position {pos}: No resume found")
                    
            except Exception as e:
                print(f"   Position {pos}: ❌ Query error - {type(e).__name__}: {e}")
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print("\nThe error is likely due to:")
        print("1. Data type mismatch (JSONB fields not properly handled)")
        print("2. Null values in required fields")
        print("3. Serialization issues with complex types")
        print("\nCheck the backend logs for the exact Python traceback!")

if __name__ == "__main__":
    asyncio.run(main())