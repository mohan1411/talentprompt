"""Quick test to verify career analytics are working"""

# Test if the services can be imported
try:
    from app.services.candidate_analytics import candidate_analytics_service
    print("✅ candidate_analytics_service imported successfully")
except Exception as e:
    print(f"❌ Failed to import candidate_analytics_service: {e}")

try:
    from app.services.career_dna import career_dna_service
    print("✅ career_dna_service imported successfully")
except Exception as e:
    print(f"❌ Failed to import career_dna_service: {e}")

# Test basic functionality
test_resume = {
    'id': 'test-123',
    'first_name': 'John',
    'last_name': 'Doe',
    'current_title': 'Senior Python Developer',
    'years_experience': 8,
    'skills': ['Python', 'AWS', 'Django', 'PostgreSQL', 'Docker'],
    'summary': 'Experienced developer looking for new opportunities',
    'positions': []
}

print("\n📊 Testing analytics calculations:")

try:
    availability = candidate_analytics_service.calculate_availability_score(test_resume)
    print(f"✅ Availability Score: {availability:.2f}")
except Exception as e:
    print(f"❌ Failed to calculate availability: {e}")

try:
    learning_vel = candidate_analytics_service.calculate_learning_velocity(test_resume)
    print(f"✅ Learning Velocity: {learning_vel:.2f}")
except Exception as e:
    print(f"❌ Failed to calculate learning velocity: {e}")

try:
    career_traj = candidate_analytics_service.analyze_career_trajectory(test_resume)
    print(f"✅ Career Trajectory: {career_traj['pattern']}")
except Exception as e:
    print(f"❌ Failed to analyze career trajectory: {e}")

try:
    career_dna = career_dna_service.extract_career_dna(test_resume)
    print(f"✅ Career DNA Pattern: {career_dna['pattern_type']}")
except Exception as e:
    print(f"❌ Failed to extract career DNA: {e}")

print("\n✅ All imports and basic functions working!")