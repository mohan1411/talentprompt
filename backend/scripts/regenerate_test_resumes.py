#!/usr/bin/env python3
"""Clear existing test resumes and regenerate with better skill distributions."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, delete

from app.core.config import settings
from app.models.user import User
from app.models.resume import Resume
from app.services.vector_search import vector_search

# Import the generate function
from generate_test_resumes import create_test_resumes


async def clear_existing_resumes(user_email: str = "promtitude@gmail.com") -> None:
    """Clear all existing resumes for the test user."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Find user
            stmt = select(User).where(User.email == user_email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User {user_email} not found!")
                return
            
            print(f"Found user: {user.email} (ID: {user.id})")
            
            # Count existing resumes
            count_stmt = select(Resume).where(Resume.user_id == user.id)
            count_result = await db.execute(count_stmt)
            existing_count = len(count_result.scalars().all())
            
            print(f"\nFound {existing_count} existing resumes")
            
            if existing_count > 0:
                print("Deleting existing resumes from PostgreSQL...")
                
                # Delete all resumes for this user
                delete_stmt = delete(Resume).where(Resume.user_id == user.id)
                await db.execute(delete_stmt)
                await db.commit()
                
                print(f"✅ Deleted {existing_count} resumes from PostgreSQL")
                
                # Clear from Qdrant
                print("\nClearing vectors from Qdrant...")
                try:
                    # Get all points for this user
                    from qdrant_client.models import Filter, FieldCondition, MatchValue
                    
                    filter_condition = Filter(
                        must=[
                            FieldCondition(
                                key="user_id",
                                match=MatchValue(value=str(user.id))
                            )
                        ]
                    )
                    
                    # Delete points
                    await vector_search.client.delete(
                        collection_name=vector_search.collection_name,
                        points_selector=filter_condition
                    )
                    
                    print("✅ Cleared vectors from Qdrant")
                except Exception as e:
                    print(f"⚠️  Warning: Error clearing Qdrant: {e}")
                    print("   You may need to manually clear the collection")
            
        finally:
            await engine.dispose()


async def verify_skill_distribution(user_email: str = "promtitude@gmail.com") -> None:
    """Verify the skill distribution in generated resumes."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Find user
            stmt = select(User).where(User.email == user_email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return
            
            # Get all resumes
            stmt = select(Resume).where(Resume.user_id == user.id)
            result = await db.execute(stmt)
            resumes = result.scalars().all()
            
            print("\n" + "="*60)
            print("SKILL DISTRIBUTION ANALYSIS")
            print("="*60)
            
            # Count skill combinations
            python_count = 0
            aws_count = 0
            python_aws_count = 0
            senior_python_aws_count = 0
            
            for resume in resumes:
                if resume.skills:
                    skills_lower = [s.lower() for s in resume.skills]
                    has_python = "python" in skills_lower
                    has_aws = "aws" in skills_lower
                    
                    if has_python:
                        python_count += 1
                    if has_aws:
                        aws_count += 1
                    if has_python and has_aws:
                        python_aws_count += 1
                        if "senior" in (resume.current_title or "").lower():
                            senior_python_aws_count += 1
            
            print(f"Total resumes: {len(resumes)}")
            print(f"Resumes with Python: {python_count} ({python_count/len(resumes)*100:.1f}%)")
            print(f"Resumes with AWS: {aws_count} ({aws_count/len(resumes)*100:.1f}%)")
            print(f"Resumes with Python AND AWS: {python_aws_count} ({python_aws_count/len(resumes)*100:.1f}%)")
            print(f"Senior developers with Python AND AWS: {senior_python_aws_count}")
            
            # Show first 5 Python+AWS candidates
            print("\nFirst 5 candidates with Python AND AWS:")
            shown = 0
            for resume in resumes:
                if resume.skills:
                    skills_lower = [s.lower() for s in resume.skills]
                    if "python" in skills_lower and "aws" in skills_lower:
                        print(f"  - {resume.first_name} {resume.last_name}: {resume.current_title}")
                        print(f"    Skills: {', '.join(resume.skills[:8])}...")
                        shown += 1
                        if shown >= 5:
                            break
            
        finally:
            await engine.dispose()


async def main():
    """Main function."""
    print("="*70)
    print("REGENERATE TEST RESUMES WITH BETTER SKILL DISTRIBUTIONS")
    print("="*70)
    
    # Clear existing resumes
    print("\nStep 1: Clearing existing test resumes...")
    await clear_existing_resumes()
    
    # Generate new resumes
    print("\nStep 2: Generating new test resumes with better skill combinations...")
    await create_test_resumes(100)
    
    # Verify distribution
    print("\nStep 3: Verifying skill distribution...")
    await verify_skill_distribution()
    
    print("\n✅ Resume regeneration complete!")
    print("\nThe new test data ensures:")
    print("  - At least 30% of resumes have common skill combinations")
    print("  - First 5 resumes definitely have Python + AWS")
    print("  - More realistic skill groupings")
    print("\nYou can now test searches like 'Senior Python Developer with AWS'")


if __name__ == "__main__":
    asyncio.run(main())