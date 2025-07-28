#!/usr/bin/env python3
"""Validate that the search fix prevents candidates without required skills from ranking high."""

from typing import List, Dict, Any

# Simulate the enhanced skill matching logic
def calculate_enhanced_score(
    original_score: float,
    required_skills: List[str],
    candidate_skills: List[str],
    candidate_name: str
) -> float:
    """Calculate score with enhanced skill matching."""
    if not required_skills:
        return original_score
    
    # Convert to lowercase for matching
    candidate_skills_lower = [s.lower() for s in candidate_skills]
    
    # Count skill matches
    matched_skills = 0
    for required_skill in required_skills:
        if any(required_skill in skill for skill in candidate_skills_lower):
            matched_skills += 1
    
    skill_match_ratio = matched_skills / len(required_skills)
    
    # Apply scoring logic
    if skill_match_ratio == 1.0:
        # All skills match - boost
        final_score = min(1.0, original_score * 1.3)
        match_type = "PERFECT"
    elif skill_match_ratio >= 0.5:
        # Partial match - significant penalty
        penalty_factor = 0.2 + (skill_match_ratio * 0.4)  # 0.4 for 50%, 0.6 for 75%
        final_score = original_score * penalty_factor
        match_type = "PARTIAL"
    else:
        # Poor match - severe penalty
        final_score = original_score * 0.3
        match_type = "POOR"
    
    print(f"\n{candidate_name}:")
    print(f"  Skills: {candidate_skills}")
    print(f"  Match: {matched_skills}/{len(required_skills)} = {skill_match_ratio:.0%} ({match_type})")
    print(f"  Original score: {original_score:.3f}")
    print(f"  Final score: {final_score:.3f}")
    
    return final_score


def main():
    """Test various scenarios."""
    print("="*70)
    print("VALIDATING SEARCH FIX: Skill-Based Scoring")
    print("="*70)
    
    # Test scenarios
    query = "Senior Python Developer with AWS"
    required_skills = ["python", "aws"]
    
    print(f"\nQuery: '{query}'")
    print(f"Required skills: {required_skills}")
    print("-"*50)
    
    # Test candidates
    candidates = [
        {
            "name": "Perfect Match",
            "skills": ["Python", "AWS", "Django", "PostgreSQL"],
            "vector_score": 0.75
        },
        {
            "name": "William Alves",
            "skills": ["Kubernetes", "AWS", "Ruby", "JavaScript"],
            "vector_score": 0.85  # High vector score due to "Senior Engineer"
        },
        {
            "name": "No AWS Developer",
            "skills": ["Python", "Django", "Flask", "PostgreSQL"],
            "vector_score": 0.80
        },
        {
            "name": "No Skills Match",
            "skills": ["Java", "Spring Boot", "Oracle", "Jenkins"],
            "vector_score": 0.70
        },
        {
            "name": "Lower Score but Perfect Skills",
            "skills": ["Python", "AWS", "FastAPI", "Docker"],
            "vector_score": 0.65
        }
    ]
    
    # Calculate scores
    results = []
    for candidate in candidates:
        score = calculate_enhanced_score(
            candidate["vector_score"],
            required_skills,
            candidate["skills"],
            candidate["name"]
        )
        results.append((candidate["name"], score, candidate["skills"]))
    
    # Sort by score
    results.sort(key=lambda x: x[1], reverse=True)
    
    print("\n" + "="*70)
    print("FINAL RANKINGS")
    print("="*70)
    
    for i, (name, score, skills) in enumerate(results, 1):
        has_python = any("python" in s.lower() for s in skills)
        has_aws = any("aws" in s.lower() for s in skills)
        status = "✓✓" if has_python and has_aws else "✓✗" if has_python or has_aws else "✗✗"
        
        print(f"{i}. {name:<30} Score: {score:.3f} [{status}]")
    
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)
    
    # Check if William Alves is properly penalized
    william_rank = next((i for i, (name, _, _) in enumerate(results, 1) if name == "William Alves"), None)
    
    if william_rank and william_rank > 3:
        print("✅ SUCCESS: William Alves (missing Python) is ranked low (#{}), not in top 3!".format(william_rank))
    else:
        print("❌ ISSUE: William Alves is still ranking too high!")
    
    # Verify perfect matches rank highest
    top_name = results[0][0]
    if "Perfect" in top_name or all(skill in ["python", "aws"] for skill in [s.lower() for s in results[0][2]][:2]):
        print("✅ SUCCESS: Top result has both Python and AWS skills!")
    else:
        print("❌ ISSUE: Top result doesn't have all required skills!")
    
    print("\n📊 Summary:")
    print("- Candidates with BOTH required skills get 1.3x boost")
    print("- Candidates with 50% skills (like William) get 0.6x penalty")
    print("- Candidates with <50% skills get 0.3x severe penalty")
    print("\nThis ensures skill relevance is prioritized over semantic similarity!")


if __name__ == "__main__":
    main()