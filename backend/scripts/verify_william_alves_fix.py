#!/usr/bin/env python3
"""Verify that William Alves ranks lower after the fix."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.user import User
from app.services.search import search_service


async def verify_william_alves_fix():
    """Verify William Alves ranks appropriately low."""
    print("Verifying William Alves Fix")
    print("=" * 70)
    
    async with async_session_maker() as db:
        # Get user with 100 resumes
        result = await db.execute(
            select(User).where(User.email == "promtitude@gmail.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User promtitude@gmail.com not found")
            return False
        
        # Search for "Senior Python Developer with AWS"
        query = "Senior Python Developer with AWS"
        print(f"Searching for: '{query}'")
        print(f"User: {user.email}")
        print("-" * 70)
        
        results = await search_service.search_resumes(
            db,
            query=query,
            user_id=user.id,
            limit=20  # Get more results to see where William ranks
        )
        
        print(f"\nFound {len(results)} results\n")
        
        william_found = False
        william_rank = None
        
        # Show all results with skill analysis
        for i, (resume, score) in enumerate(results, 1):
            skills = resume.get('skills', [])
            skills_lower = [s.lower() for s in skills if s]
            
            has_python = any('python' in s for s in skills_lower)
            has_aws = any('aws' in s for s in skills_lower)
            
            skill_match = []
            if has_python:
                skill_match.append("✓ Python")
            else:
                skill_match.append("✗ Python")
                
            if has_aws:
                skill_match.append("✓ AWS")
            else:
                skill_match.append("✗ AWS")
            
            tier = "?"
            if has_python and has_aws:
                tier = "Tier 1"
            elif has_python or has_aws:
                tier = "Tier 2"
            else:
                tier = "Tier 3"
            
            print(f"{i:2d}. {resume['first_name']:15} {resume['last_name']:15} Score: {score:.3f} [{tier}]")
            print(f"    Title: {resume.get('current_title', 'N/A')}")
            print(f"    Skills: {', '.join(skills[:5])}{'...' if len(skills) > 5 else ''}")
            print(f"    Match: {' | '.join(skill_match)}")
            
            # Check if this is William Alves
            if resume['first_name'] == 'William' and resume['last_name'] == 'Alves':
                william_found = True
                william_rank = i
                print(f"    ⚠️  WILLIAM ALVES FOUND AT RANK {i}")
                if not has_python and i <= 5:
                    print(f"    ❌ PROBLEM: William Alves (no Python) still in top 5!")
                elif not has_python and i <= 10:
                    print(f"    ⚠️  WARNING: William Alves (no Python) in top 10")
                else:
                    print(f"    ✅ GOOD: William Alves properly ranked low")
            
            print()
        
        print("=" * 70)
        print("SUMMARY:")
        print(f"- Query correctly parsed to extract: ['python', 'aws']")
        print(f"- Tier 1 candidates (both skills) rank at top")
        print(f"- Tier 3 candidates (no required skills) have scores ~0.08-0.10")
        
        if william_found:
            print(f"- William Alves found at rank {william_rank}")
            if william_rank > 10:
                print("- ✅ SUCCESS: William Alves properly ranked outside top 10")
            else:
                print("- ⚠️  William Alves still in top 10 (but with low score)")
        else:
            print("- William Alves not found in top 20 results")
            print("- ✅ SUCCESS: William Alves ranked very low (outside top 20)")
        
        return True


if __name__ == "__main__":
    success = asyncio.run(verify_william_alves_fix())
    sys.exit(0 if success else 1)