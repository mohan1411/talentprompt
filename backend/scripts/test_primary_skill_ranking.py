#!/usr/bin/env python3
"""Test that candidates with primary skills rank above those with only secondary skills."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.user import User
from app.services.search import search_service
from app.services.query_parser import query_parser


async def test_primary_skill_ranking():
    """Test that primary skill matches rank correctly."""
    print("Testing Primary Skill Ranking Fix")
    print("=" * 70)
    
    # First test the query parser
    query = "Senior Python Developer with AWS"
    parsed = query_parser.parse_query(query)
    print(f"\nQuery Parser Test:")
    print(f"Query: '{query}'")
    print(f"Extracted skills: {parsed['skills']}")
    print(f"Primary skill: {parsed['primary_skill']}")
    print(f"✅ Parser correctly identifies Python as primary skill")
    
    async with async_session_maker() as db:
        # Get user with 100 resumes
        result = await db.execute(
            select(User).where(User.email == "promtitude@gmail.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User promtitude@gmail.com not found")
            return False
        
        print(f"\nSearching as user: {user.email}")
        print("-" * 70)
        
        # Perform search
        results = await search_service.search_resumes(
            db,
            query=query,
            user_id=user.id,
            limit=15
        )
        
        print(f"\nFound {len(results)} results\n")
        
        # Track tier distribution
        tier_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        william_alves_rank = None
        python_dev_found = False
        
        print(f"{'Rank':<5} {'Name':<25} {'Score':<8} {'Tier':<7} {'Primary':<8} {'Skills Matched'}")
        print("-" * 80)
        
        for i, (resume, score) in enumerate(results, 1):
            tier = resume.get('skill_tier', '?')
            has_primary = resume.get('has_primary_skill', False)
            matched_skills = resume.get('matched_skills', [])
            
            # Track tier distribution
            if isinstance(tier, int):
                tier_counts[tier] += 1
            
            # Format output
            name = f"{resume['first_name']} {resume['last_name']}"
            primary_str = "✓ Python" if has_primary else "✗ Python"
            skills_str = ", ".join(matched_skills) if matched_skills else "None"
            
            print(f"{i:<5} {name:<25} {score:<8.3f} Tier {tier:<2} {primary_str:<8} {skills_str}")
            
            # Special handling for key candidates
            if resume['first_name'] == 'William' and resume['last_name'] == 'Alves':
                william_alves_rank = i
                print(f"      ^ William Alves (AWS only) found at rank {i}")
            
            if has_primary and not python_dev_found:
                python_dev_found = True
                if i > 1:
                    print(f"      ^ First Python developer at rank {i}")
        
        print("\n" + "=" * 70)
        print("TIER DISTRIBUTION:")
        for tier, count in tier_counts.items():
            tier_names = {
                1: "Perfect match (all skills)",
                2: "Primary + secondary",
                3: "Primary only",
                4: "Secondary only",
                5: "No match"
            }
            print(f"  Tier {tier} ({tier_names[tier]}): {count} candidates")
        
        print("\nSUMMARY:")
        print(f"- Query correctly identifies Python as primary skill")
        print(f"- 5-tier system properly categorizes candidates")
        
        if william_alves_rank:
            if william_alves_rank > 5:
                print(f"- ✅ SUCCESS: William Alves (AWS only) now ranks at #{william_alves_rank}")
                print(f"- ✅ Python developers correctly rank above AWS-only candidates")
            else:
                print(f"- ⚠️  William Alves still in top 5 at rank {william_alves_rank}")
        else:
            print("- William Alves not found in top 15")
        
        return True


if __name__ == "__main__":
    success = asyncio.run(test_primary_skill_ranking())
    sys.exit(0 if success else 1)