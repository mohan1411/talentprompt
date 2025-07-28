#!/usr/bin/env python3
"""Debug resume visibility issues."""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    print("="*60)
    print("RESUME DEBUG TOOL")
    print("="*60)
    
    try:
        # Import after adding to path
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import select, text
        from sqlalchemy.orm import sessionmaker
        from app.models.user import User
        from app.models.resume import Resume
        
        # Get database URL
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://promtitude:promtitude123@localhost:5433/promtitude")
        
        print(f"\n1. Connecting to database...")
        engine = create_async_engine(DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Find user
            email = "promtitude@gmail.com"
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"\n❌ User {email} not found!")
                
                # List all users
                result = await session.execute(select(User).limit(10))
                users = result.scalars().all()
                print("\nAvailable users:")
                for u in users:
                    print(f"  - {u.email} (ID: {u.id})")
            else:
                print(f"\n✅ Found user: {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Name: {user.full_name}")
                print(f"   Active: {user.is_active}")
                
                # Count resumes for this user
                result = await session.execute(
                    select(Resume).where(Resume.user_id == user.id)
                )
                resumes = result.scalars().all()
                
                print(f"\n2. Resume count for {email}: {len(resumes)}")
                
                if resumes:
                    print("\n   First 5 resumes:")
                    for i, resume in enumerate(resumes[:5]):
                        print(f"   {i+1}. {resume.first_name} {resume.last_name}")
                        print(f"      Title: {resume.current_title}")
                        print(f"      Status: {resume.status}")
                        print(f"      Created: {resume.created_at}")
                else:
                    print("\n   ⚠️ No resumes found for this user!")
                    
                    # Check total resumes in system
                    result = await session.execute(select(Resume))
                    all_resumes = result.scalars().all()
                    print(f"\n3. Total resumes in database: {len(all_resumes)}")
                    
                    if all_resumes:
                        # Find which users have resumes
                        user_resume_map = {}
                        for resume in all_resumes:
                            if resume.user_id not in user_resume_map:
                                user_resume_map[resume.user_id] = 0
                            user_resume_map[resume.user_id] += 1
                        
                        print("\n   Users with resumes:")
                        for user_id, count in list(user_resume_map.items())[:5]:
                            result = await session.execute(
                                select(User).where(User.id == user_id)
                            )
                            u = result.scalar_one_or_none()
                            if u:
                                print(f"   - {u.email}: {count} resumes")
                
                # Save user ID to file for reference
                with open('user_id.txt', 'w') as f:
                    f.write(f"User ID for {email}: {user.id}\n")
                print(f"\n✅ User ID saved to user_id.txt")
                
                return str(user.id)
                
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("\nMake sure you're in the backend virtual environment:")
        print("  cd backend")
        print("  .\\venv\\Scripts\\activate  (Windows)")
        print("  source venv/bin/activate  (Linux/Mac)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    user_id = asyncio.run(main())
    
    if user_id:
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print(f"\n1. To generate a working token, run:")
        print(f"   python generate_working_token.py {user_id}")
        print(f"\n2. To import test resumes for this user, run:")
        print(f"   python import_test_resumes.py --user-id {user_id}")