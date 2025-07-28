#!/usr/bin/env python3
"""Test the tiered search system that prioritizes skill completeness."""

from typing import List, Dict, Any, Tuple

def calculate_tiered_score(
    original_score: float,
    required_skills: List[str],
    candidate_skills: List[str],
    candidate_name: str
) -> Tuple[float, int]:
    """Calculate score and tier with enhanced skill matching."""
    if not required_skills:
        return original_score, 999
    
    # Convert to lowercase for matching
    candidate_skills_lower = [s.lower() for s in candidate_skills]
    
    # Count skill matches
    matched_skills = 0
    for required_skill in required_skills:
        if any(required_skill in skill for skill in candidate_skills_lower):
            matched_skills += 1
    
    skill_match_ratio = matched_skills / len(required_skills)
    
    # Apply scoring logic with tiers
    if skill_match_ratio == 1.0:
        # Tier 1: All skills match - boost
        final_score = min(1.0, original_score * 1.3)
        tier = 1
        match_type = "PERFECT"
    elif skill_match_ratio >= 0.5:
        # Tier 2: Partial match - penalty
        penalty_factor = 0.2 + (skill_match_ratio * 0.4)
        final_score = original_score * penalty_factor
        tier = 2
        match_type = "PARTIAL"
    else:
        # Tier 3: Poor match - severe penalty
        final_score = original_score * 0.3
        tier = 3
        match_type = "POOR"
    
    print(f"\n{candidate_name}:")
    print(f"  Skills: {', '.join(candidate_skills[:5])}{'...' if len(candidate_skills) > 5 else ''}")
    print(f"  Match: {matched_skills}/{len(required_skills)} = {skill_match_ratio:.0%} ({match_type})")
    print(f"  Tier: {tier} | Original: {original_score:.3f} | Final: {final_score:.3f}")
    
    return final_score, tier


def main():
    """Test tiered search system."""
    print("="*70)
    print("TIERED SEARCH SYSTEM TEST")
    print("="*70)
    
    query = "Senior Python Developer with AWS"
    required_skills = ["python", "aws"]
    
    print(f"\nQuery: '{query}'")
    print(f"Required skills: {required_skills}")
    print("\n" + "-"*70)
    print("CANDIDATE ANALYSIS")
    print("-"*70)
    
    # Extended test candidates
    candidates = [
        # Tier 1: Perfect matches
        {"name": "Perfect Match (High Score)", "skills": ["Python", "AWS", "Django", "PostgreSQL"], "vector_score": 0.75},
        {"name": "Perfect Match (Low Score)", "skills": ["Python", "AWS", "FastAPI", "Docker"], "vector_score": 0.55},
        
        # Tier 2: Partial matches
        {"name": "William Alves", "skills": ["Kubernetes", "AWS", "Ruby", "JavaScript"], "vector_score": 0.85},
        {"name": "Python Only", "skills": ["Python", "Django", "Flask", "PostgreSQL"], "vector_score": 0.80},
        {"name": "AWS Only", "skills": ["AWS", "Docker", "Kubernetes", "Terraform"], "vector_score": 0.70},
        
        # Tier 3: Poor matches
        {"name": "No Match (High Score)", "skills": ["Java", "Spring Boot", "Oracle", "Jenkins"], "vector_score": 0.75},
        {"name": "No Match (Low Score)", "skills": ["PHP", "Laravel", "MySQL", "Redis"], "vector_score": 0.60},
        
        # Edge cases
        {"name": "Many Skills Perfect", "skills": ["Python", "AWS", "React", "Node.js", "Docker", "K8s", "ML"], "vector_score": 0.65},
        {"name": "Senior Title No Skills", "skills": ["C++", "Embedded", "RTOS", "ARM"], "vector_score": 0.90},
    ]
    
    # Calculate scores and tiers
    results = []
    for candidate in candidates:
        score, tier = calculate_tiered_score(
            candidate["vector_score"],
            required_skills,
            candidate["skills"],
            candidate["name"]
        )
        results.append((candidate["name"], score, tier, candidate["skills"]))
    
    # Sort by tier first (ascending), then by score (descending)
    results.sort(key=lambda x: (x[2], -x[1]))
    
    print("\n" + "="*70)
    print("FINAL RANKINGS (Tiered System)")
    print("="*70)
    print("\nRank | Tier | Score  | Name                          | Skills Match")
    print("-"*70)
    
    for i, (name, score, tier, skills) in enumerate(results, 1):
        has_python = any("python" in s.lower() for s in skills)
        has_aws = any("aws" in s.lower() for s in skills)
        
        if has_python and has_aws:
            match_icon = "✓✓"
        elif has_python:
            match_icon = "✓✗"
        elif has_aws:
            match_icon = "✗✓"
        else:
            match_icon = "✗✗"
        
        tier_label = {1: "Perfect", 2: "Partial", 3: "Poor"}[tier]
        print(f"{i:4} | {tier_label:7} | {score:.3f} | {name:30} | {match_icon}")
    
    print("\n" + "="*70)
    print("KEY INSIGHTS")
    print("="*70)
    
    # Analysis
    william_rank = next((i for i, (name, _, _, _) in enumerate(results, 1) if name == "William Alves"), None)
    top_tier = results[0][2] if results else None
    
    print(f"\n1. Tiered Ranking System:")
    print(f"   - Tier 1 (Perfect): All required skills present")
    print(f"   - Tier 2 (Partial): Some required skills missing")
    print(f"   - Tier 3 (Poor): Most/all required skills missing")
    
    print(f"\n2. William Alves Status:")
    print(f"   - Ranked: #{william_rank} (Tier 2 - Partial Match)")
    print(f"   - Has AWS but missing Python")
    print(f"   - Despite high vector score (0.85), ranked below ALL perfect matches")
    
    if top_tier == 1:
        print(f"\n3. ✅ SUCCESS: Top results all have BOTH Python AND AWS!")
        print(f"   - Even candidates with lower vector scores rank higher if they have all skills")
    
    print(f"\n4. Score Penalties:")
    print(f"   - Perfect match: 1.3x boost")
    print(f"   - 50% match (like William): 0.4x penalty (60% reduction)")
    print(f"   - <50% match: 0.3x penalty (70% reduction)")
    
    # Count candidates by tier
    tier_counts = {1: 0, 2: 0, 3: 0}
    for _, _, tier, _ in results:
        tier_counts[tier] += 1
    
    print(f"\n5. Distribution:")
    print(f"   - Tier 1 (Perfect): {tier_counts[1]} candidates")
    print(f"   - Tier 2 (Partial): {tier_counts[2]} candidates")
    print(f"   - Tier 3 (Poor): {tier_counts[3]} candidates")


if __name__ == "__main__":
    main()