#!/usr/bin/env python3
"""Test script to verify user data isolation is working correctly."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.models.resume import Resume
from app.models.user import User
from app.services.search import search_service


async def test_user_isolation():
    """Test that users can only see their own resumes."""
    print("\n" + "="*60)
    print("TESTING USER DATA ISOLATION")
    print("="*60)
    
    # Create database engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as db:
        try:
            # Get all users with resumes
            stmt = select(User).join(Resume).distinct()
            result = await db.execute(stmt)
            users = result.scalars().all()
            
            print(f"\nFound {len(users)} users with resumes")
            
            if len(users) < 2:
                print("\n⚠️  Need at least 2 users with resumes to properly test isolation")
                return
            
            # Test each user
            for i, user in enumerate(users[:2]):  # Test first 2 users
                print(f"\n{'='*40}")
                print(f"Testing User {i+1}: {user.email} (ID: {user.id})")
                print(f"{'='*40}")
                
                # Count user's resumes in database
                count_stmt = select(func.count(Resume.id)).where(Resume.user_id == user.id)
                count_result = await db.execute(count_stmt)
                db_count = count_result.scalar() or 0
                
                print(f"Database resume count: {db_count}")
                
                # Test search
                search_results = await search_service.search_resumes(
                    db=db,
                    query="software engineer python java",
                    user_id=user.id,
                    limit=100
                )
                
                print(f"Search returned: {len(search_results)} results")
                
                # Verify all results belong to this user
                incorrect_results = 0
                for resume_data, score in search_results:
                    # Get the actual resume to check user_id
                    resume_stmt = select(Resume).where(Resume.id == resume_data["id"])
                    resume_result = await db.execute(resume_stmt)
                    resume = resume_result.scalar_one_or_none()
                    
                    if resume and resume.user_id != user.id:
                        print(f"  ❌ SECURITY BREACH: Resume {resume.id} belongs to user {resume.user_id}, not {user.id}!")
                        incorrect_results += 1
                
                if incorrect_results == 0:
                    print(f"  ✅ All {len(search_results)} results correctly belong to user {user.id}")
                else:
                    print(f"  ❌ Found {incorrect_results} resumes from other users!")
                
                # Test search suggestions
                suggestions = await search_service.get_search_suggestions(
                    db=db,
                    query="python",
                    user_id=user.id
                )
                print(f"\nSearch suggestions: {len(suggestions)} suggestions")
                
                # Test popular tags
                tags = await search_service.get_popular_tags(
                    db=db,
                    user_id=user.id,
                    limit=10
                )
                print(f"Popular tags: {len(tags)} tags")
            
            print("\n" + "="*60)
            print("TEST COMPLETE")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


async def test_cross_user_search():
    """Test that one user CANNOT see another user's resumes."""
    print("\n" + "="*60)
    print("TESTING CROSS-USER SEARCH PREVENTION")
    print("="*60)
    
    # Create database engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as db:
        try:
            # Get two different users
            stmt = select(User).join(Resume).distinct().limit(2)
            result = await db.execute(stmt)
            users = result.scalars().all()
            
            if len(users) < 2:
                print("\n⚠️  Need at least 2 users to test cross-user prevention")
                return
            
            user1, user2 = users[0], users[1]
            
            print(f"\nUser 1: {user1.email} (ID: {user1.id})")
            print(f"User 2: {user2.email} (ID: {user2.id})")
            
            # Get a specific resume from user2
            user2_resume_stmt = select(Resume).where(Resume.user_id == user2.id).limit(1)
            user2_resume_result = await db.execute(user2_resume_stmt)
            user2_resume = user2_resume_result.scalar_one_or_none()
            
            if not user2_resume:
                print(f"\n⚠️  User 2 has no resumes")
                return
            
            print(f"\nUser 2 has resume: {user2_resume.first_name} {user2_resume.last_name}")
            
            # Try to search for user2's resume content as user1
            search_query = f"{user2_resume.first_name} {user2_resume.last_name}"
            if user2_resume.skills:
                search_query += f" {' '.join(user2_resume.skills[:3])}"
            
            print(f"\nSearching as User 1 for: '{search_query}'")
            
            results = await search_service.search_resumes(
                db=db,
                query=search_query,
                user_id=user1.id,
                limit=100
            )
            
            print(f"Search returned: {len(results)} results")
            
            # Check if any results are from user2
            found_user2_resume = False
            for resume_data, score in results:
                if resume_data["id"] == str(user2_resume.id):
                    found_user2_resume = True
                    print(f"\n❌ SECURITY BREACH: User 1 can see User 2's resume!")
                    break
            
            if not found_user2_resume:
                print(f"\n✅ PASS: User 1 cannot see User 2's resume (as expected)")
            
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


async def main():
    """Run all tests."""
    await test_user_isolation()
    await test_cross_user_search()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("If you see any ❌ marks above, the security fix is not working properly!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())