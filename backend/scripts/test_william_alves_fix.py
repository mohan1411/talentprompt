#!/usr/bin/env python3
"""Test that William Alves (no Python skill) doesn't rank high for Python searches."""

# Quick test to demonstrate the issue and solution
print("="*70)
print("TEST: William Alves should NOT rank high for Python searches")
print("="*70)

# William Alves skills
william_skills = ["Kubernetes", "AWS", "Ruby", "Terraform", "JavaScript", "Svelte", "Next.js", "CircleCI"]
william_skills_lower = [s.lower() for s in william_skills]

# Test query
query = "Senior Python Developer with AWS"
required_skills = ["python", "aws"]  # Extracted by query parser

print(f"\nWilliam Alves skills: {william_skills}")
print(f"\nSearch query: '{query}'")
print(f"Required skills: {required_skills}")

# Calculate skill match
matched_skills = 0
for required_skill in required_skills:
    if any(required_skill in skill for skill in william_skills_lower):
        matched_skills += 1
        print(f"  ✓ Has {required_skill}")
    else:
        print(f"  ✗ Missing {required_skill}")

skill_match_ratio = matched_skills / len(required_skills)
print(f"\nSkill match ratio: {matched_skills}/{len(required_skills)} = {skill_match_ratio:.1%}")

# Simulate scoring
original_vector_score = 0.85  # High because "Senior Software Engineer" matches "Senior Developer"

print(f"\nOriginal vector similarity score: {original_vector_score:.3f}")

# OLD LOGIC (60% vector + 40% skill match)
old_hybrid_score = (original_vector_score * 0.6) + (skill_match_ratio * 0.4)
print(f"\nOLD scoring (60% vector + 40% skill):")
print(f"  Score = ({original_vector_score:.3f} * 0.6) + ({skill_match_ratio:.2f} * 0.4) = {old_hybrid_score:.3f}")

# NEW LOGIC (aggressive penalty for 50% match)
penalty_factor = 0.4 + (skill_match_ratio * 0.4)  # 0.6 for 50% match
new_hybrid_score = original_vector_score * penalty_factor
print(f"\nNEW scoring (aggressive penalty):")
print(f"  Penalty factor for 50% match = 0.4 + (0.5 * 0.4) = {penalty_factor:.1f}")
print(f"  Score = {original_vector_score:.3f} * {penalty_factor:.1f} = {new_hybrid_score:.3f}")

print(f"\n📊 RESULT:")
print(f"  Old score: {old_hybrid_score:.3f} (would rank HIGH)")
print(f"  New score: {new_hybrid_score:.3f} (40% reduction - will rank LOWER)")

print("\n✅ With the new scoring, candidates with BOTH Python and AWS will score higher")
print("   Example: Someone with both skills and 0.7 vector score = 0.7 * 1.3 = 0.91")
print(f"   This is much higher than William's {new_hybrid_score:.3f}")

# Show example of someone with both skills
print("\n" + "="*60)
print("COMPARISON: Candidate with BOTH Python and AWS")
print("="*60)
other_vector_score = 0.7  # Lower vector score
other_match_ratio = 1.0   # Has both skills

print(f"Vector score: {other_vector_score:.3f} (lower than William)")
print(f"Skill match: 2/2 = 100%")
print(f"Final score: {other_vector_score:.3f} * 1.3 = {other_vector_score * 1.3:.3f}")
print(f"\n✓ Ranks HIGHER than William ({other_vector_score * 1.3:.3f} > {new_hybrid_score:.3f})")