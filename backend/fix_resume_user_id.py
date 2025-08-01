#!/usr/bin/env python3
"""
Fix resumes that don't have user_id set.
This script identifies and fixes resumes without user_id which causes indexing failures.
"""

import asyncio
import os
import sys
from datetime import datetime
from uuid import UUID

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.resume import Resume
from app.models.user import User
from app.services.vector_search import vector_search
from app.services.reindex_service import ReindexService


async def find_resumes_without_user_id(db: AsyncSession):
    """Find resumes that don't have a user_id."""
    print("🔍 Searching for resumes without user_id...")
    
    # Query for resumes where user_id is NULL
    stmt = select(Resume).where(Resume.user_id == None)
    result = await db.execute(stmt)
    resumes = result.scalars().all()
    
    if resumes:
        print(f"❌ Found {len(resumes)} resumes without user_id:")
        for resume in resumes[:10]:  # Show first 10
            print(f"   - ID: {resume.id}, Name: {resume.first_name} {resume.last_name}, Created: {resume.created_at}")
        if len(resumes) > 10:
            print(f"   ... and {len(resumes) - 10} more")
    else:
        print("✅ All resumes have user_id set")
    
    return resumes


async def find_specific_resume(db: AsyncSession, resume_id: str):
    """Find a specific resume by ID."""
    try:
        resume_uuid = UUID(resume_id)
        stmt = select(Resume).where(Resume.id == resume_uuid)
        result = await db.execute(stmt)
        resume = result.scalar_one_or_none()
        
        if resume:
            print(f"\n📄 Found resume {resume_id}:")
            print(f"   Name: {resume.first_name} {resume.last_name}")
            print(f"   User ID: {resume.user_id}")
            print(f"   Status: {resume.status}")
            print(f"   Parse Status: {resume.parse_status}")
            print(f"   Created: {resume.created_at}")
            
            # Check if user exists
            if resume.user_id:
                user_stmt = select(User).where(User.id == resume.user_id)
                user_result = await db.execute(user_stmt)
                user = user_result.scalar_one_or_none()
                if user:
                    print(f"   User: {user.email} ({user.full_name})")
                else:
                    print(f"   ⚠️  User ID {resume.user_id} not found in users table!")
        else:
            print(f"❌ Resume {resume_id} not found")
            
        return resume
    except ValueError:
        print(f"❌ Invalid resume ID format: {resume_id}")
        return None


async def fix_orphaned_resumes(db: AsyncSession, assign_to_user_id: Optional[UUID] = None):
    """Fix resumes without user_id by assigning them to a user."""
    resumes_without_user = await find_resumes_without_user_id(db)
    
    if not resumes_without_user:
        return
    
    if not assign_to_user_id:
        # Find a suitable user to assign orphaned resumes to
        print("\n🔍 Finding a user to assign orphaned resumes to...")
        
        # Try to find an admin user or the first user
        stmt = select(User).where(User.is_active == True).order_by(User.created_at).limit(1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ No active users found in the database!")
            return
        
        print(f"📧 Will assign to user: {user.email} (ID: {user.id})")
        assign_to_user_id = user.id
    
    # Update resumes
    print(f"\n🔧 Updating {len(resumes_without_user)} resumes...")
    
    for resume in resumes_without_user:
        resume.user_id = assign_to_user_id
        print(f"   ✓ Updated resume {resume.id}")
    
    await db.commit()
    print("✅ All orphaned resumes have been assigned a user_id")
    
    # Reindex the fixed resumes
    print("\n🔄 Reindexing fixed resumes...")
    reindex_service = ReindexService()
    
    for resume in resumes_without_user:
        try:
            success = await reindex_service.reindex_resume(db, resume)
            if success:
                print(f"   ✓ Reindexed resume {resume.id}")
            else:
                print(f"   ⚠️  Failed to reindex resume {resume.id}")
        except Exception as e:
            print(f"   ❌ Error reindexing resume {resume.id}: {e}")


async def check_indexing_errors(db: AsyncSession):
    """Check for resumes that might have indexing errors."""
    print("\n🔍 Checking for resumes with potential indexing issues...")
    
    # Find resumes that are active but might not be indexed
    stmt = select(Resume).where(
        and_(
            Resume.status == 'active',
            Resume.parse_status == 'completed',
            Resume.user_id != None
        )
    ).limit(10)
    
    result = await db.execute(stmt)
    resumes = result.scalars().all()
    
    print(f"📊 Checking {len(resumes)} sample resumes...")
    
    for resume in resumes:
        # Check if indexed in Qdrant
        try:
            # Try to retrieve from Qdrant
            points = vector_search.client.retrieve(
                collection_name=vector_search.collection_name,
                ids=[str(resume.id)]
            )
            
            if points:
                point = points[0]
                user_id_in_qdrant = point.payload.get('user_id')
                if user_id_in_qdrant != str(resume.user_id):
                    print(f"   ⚠️  Resume {resume.id} has mismatched user_id: DB={resume.user_id}, Qdrant={user_id_in_qdrant}")
                else:
                    print(f"   ✓ Resume {resume.id} properly indexed")
            else:
                print(f"   ❌ Resume {resume.id} not found in Qdrant")
                
        except Exception as e:
            print(f"   ❌ Error checking resume {resume.id}: {e}")


async def main():
    """Main function."""
    print("🏥 Resume User ID Fix Tool")
    print("=" * 60)
    
    # Check for specific resume if provided
    if len(sys.argv) > 1:
        resume_id = sys.argv[1]
        print(f"Checking specific resume: {resume_id}")
        
        async with async_session_maker() as db:
            resume = await find_specific_resume(db, resume_id)
            
            if resume and not resume.user_id:
                print("\n⚠️  This resume has no user_id!")
                response = input("Do you want to fix this resume? (y/n): ")
                if response.lower() == 'y':
                    await fix_orphaned_resumes(db)
    else:
        # General check and fix
        async with async_session_maker() as db:
            # Find orphaned resumes
            orphaned = await find_resumes_without_user_id(db)
            
            if orphaned:
                print("\n⚠️  Found resumes without user_id!")
                response = input("Do you want to fix these resumes? (y/n): ")
                if response.lower() == 'y':
                    await fix_orphaned_resumes(db)
            
            # Check for indexing issues
            await check_indexing_errors(db)
    
    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())