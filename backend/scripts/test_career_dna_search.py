#!/usr/bin/env python3
"""
Test script to verify Career DNA and analytics are working in search results.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_engine, get_async_db
from app.models.user import User
from app.models.resume import Resume
from app.services.progressive_search import progressive_search


async def test_career_dna_search():
    """Test progressive search with Career DNA analytics."""
    print("\n=== Testing Career DNA in Progressive Search ===\n")
    
    async with AsyncSession(async_engine) as db:
        # Get test user
        stmt = select(User).where(User.email == "promtitude@gmail.com")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ Test user not found")
            return
        
        print(f"✅ Found user: {user.email}")
        
        # Test search query
        query = "Senior Python Developer with AWS"
        print(f"\n🔍 Searching for: '{query}'")
        
        # Perform progressive search
        stage_count = 0
        async for stage_result in progressive_search.search_progressive(
            db=db,
            query=query,
            user_id=user.id,
            limit=5
        ):
            stage_count += 1
            stage_name = stage_result['stage']
            result_count = stage_result['count']
            
            print(f"\n📊 Stage {stage_count}: {stage_name.upper()} - {result_count} results")
            
            # Check first few results for analytics data
            for i, (resume_data, score) in enumerate(stage_result['results'][:3]):
                print(f"\n  Result {i+1}: {resume_data['first_name']} {resume_data['last_name']}")
                print(f"  - Score: {score:.2f}")
                print(f"  - Title: {resume_data.get('current_title', 'N/A')}")
                
                # Check for analytics data
                availability = resume_data.get('availability_score')
                learning_vel = resume_data.get('learning_velocity')
                career_traj = resume_data.get('career_trajectory')
                
                if availability is not None:
                    availability_label = "Available" if availability > 0.7 else "Maybe" if availability > 0.4 else "Unlikely"
                    print(f"  - Availability: {availability:.2f} ({availability_label})")
                else:
                    print(f"  - Availability: Not calculated")
                
                if learning_vel is not None:
                    learning_label = "Fast learner" if learning_vel > 0.7 else "Average" if learning_vel > 0.4 else "Steady"
                    print(f"  - Learning Velocity: {learning_vel:.2f} ({learning_label})")
                else:
                    print(f"  - Learning Velocity: Not calculated")
                
                if career_traj:
                    print(f"  - Career DNA:")
                    print(f"    * Pattern: {career_traj['pattern']}")
                    print(f"    * Level: {career_traj['current_level']}")
                    print(f"    * Years to current: {career_traj['years_to_current']}")
                    print(f"    * Trajectory: {'Ascending' if career_traj['is_ascending'] else 'Stable'}")
                else:
                    print(f"  - Career DNA: Not calculated")
            
            # Show which stage adds the analytics
            if stage_name == 'enhanced' and stage_result['results']:
                first_result = stage_result['results'][0][0]
                if first_result.get('career_trajectory'):
                    print("\n✅ Career DNA data is being added in the ENHANCED stage!")
                else:
                    print("\n⚠️  Enhanced stage completed but no Career DNA data found")
        
        print("\n=== Search Complete ===")
        
        # Also test the analytics service directly
        print("\n\n=== Testing Analytics Service Directly ===")
        
        # Get a sample resume
        stmt = select(Resume).where(
            Resume.user_id == user.id,
            Resume.status == 'active'
        ).limit(1)
        result = await db.execute(stmt)
        sample_resume = result.scalar_one_or_none()
        
        if sample_resume:
            from app.services.candidate_analytics import candidate_analytics_service
            
            resume_dict = {
                'id': str(sample_resume.id),
                'first_name': sample_resume.first_name,
                'last_name': sample_resume.last_name,
                'current_title': sample_resume.current_title,
                'years_experience': sample_resume.years_experience,
                'skills': sample_resume.skills or [],
                'summary': sample_resume.summary,
                'positions': []  # Would need to load from work history
            }
            
            # Test analytics calculations
            availability = candidate_analytics_service.calculate_availability_score(resume_dict)
            learning_vel = candidate_analytics_service.calculate_learning_velocity(resume_dict)
            career_traj = candidate_analytics_service.analyze_career_trajectory(resume_dict)
            
            print(f"\n📊 Direct Analytics Test for: {sample_resume.first_name} {sample_resume.last_name}")
            print(f"  - Availability Score: {availability:.2f}")
            print(f"  - Learning Velocity: {learning_vel:.2f}")
            print(f"  - Career Trajectory: {career_traj}")


if __name__ == "__main__":
    print("Starting Career DNA search test...")
    asyncio.run(test_career_dna_search())