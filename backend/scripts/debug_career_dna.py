#!/usr/bin/env python3
"""
Debug script to test Career DNA extraction locally.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.career_dna import career_dna_service

# Test resume data
test_resume = {
    "first_name": "John",
    "last_name": "Doe",
    "current_title": "Senior Python Developer",
    "years_experience": 8,
    "skills": [
        "Python", "Django", "Flask", "AWS", "Docker", "Kubernetes",
        "PostgreSQL", "Redis", "React", "JavaScript", "Git",
        "Machine Learning", "TensorFlow", "Pandas", "NumPy",
        "REST APIs", "Microservices", "CI/CD", "Agile", "Leadership"
    ],
    "positions": [
        {
            "title": "Senior Python Developer",
            "company": "TechCorp",
            "start_date": "2021-01-01",
            "industry": "Technology"
        },
        {
            "title": "Python Developer",
            "company": "StartupXYZ",
            "start_date": "2018-06-01",
            "end_date": "2020-12-31",
            "industry": "Technology"
        },
        {
            "title": "Junior Developer",
            "company": "WebAgency",
            "start_date": "2016-03-01",
            "end_date": "2018-05-31",
            "industry": "Technology"
        }
    ],
    "certifications": ["AWS Certified Developer", "Python Institute PCAP"],
    "summary": "Experienced Python developer with strong background in cloud technologies and machine learning."
}

def main():
    """Test career DNA extraction."""
    print("Testing Career DNA Extraction")
    print("=" * 60)
    
    # Extract career DNA
    try:
        career_dna = career_dna_service.extract_career_dna(test_resume)
        
        print(f"\nCandidate: {test_resume['first_name']} {test_resume['last_name']}")
        print(f"Current Role: {test_resume['current_title']}")
        print(f"Experience: {test_resume['years_experience']} years")
        print(f"\nCareer DNA Profile:")
        print(f"  Pattern Type: {career_dna['pattern_type']}")
        print(f"  Progression Speed: {career_dna['progression_speed']:.2f}")
        print(f"  Skill Evolution: {career_dna['skill_evolution']}")
        print(f"  Growth Indicators: {', '.join(career_dna['growth_indicators'])}")
        print(f"  Strengths: {', '.join(career_dna['strengths'])}")
        print(f"  Unique Traits: {', '.join(career_dna['unique_traits'])}")
        print(f"\nKey Transitions:")
        for transition in career_dna['key_transitions']:
            print(f"  - {transition['description']}")
        
        print(f"\nDNA Vector (first 10 elements): {career_dna['DNA_vector'][:10]}")
        
        # Test with another profile for comparison
        test_resume2 = test_resume.copy()
        test_resume2["first_name"] = "Jane"
        test_resume2["last_name"] = "Smith"
        test_resume2["current_title"] = "Staff Software Engineer"
        test_resume2["years_experience"] = 5
        
        career_dna2 = career_dna_service.extract_career_dna(test_resume2)
        
        # Calculate similarity
        similarity = career_dna_service.calculate_dna_similarity(career_dna, career_dna2)
        
        print(f"\n\nSimilarity between {test_resume['first_name']} and {test_resume2['first_name']}: {similarity:.2f}")
        
        print("\n✓ Career DNA extraction working correctly!")
        
    except Exception as e:
        print(f"\n✗ Error extracting career DNA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()