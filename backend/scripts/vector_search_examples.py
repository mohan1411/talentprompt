#!/usr/bin/env python3
"""Vector search examples for testing different query types."""

import asyncio
import sys
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.user import User
from app.services.search import search_service
from app.services.query_parser import query_parser


# Example search queries organized by category
SEARCH_EXAMPLES = {
    "Role-Based Searches": [
        "Senior Python Developer",
        "Full Stack Developer",
        "DevOps Engineer",
        "Data Scientist",
        "Machine Learning Engineer",
        "Frontend Developer",
        "Backend Engineer",
        "Cloud Architect",
        "Mobile Developer",
        "QA Engineer"
    ],
    
    "Skill-Specific Searches": [
        "Python",
        "JavaScript React",
        "Java Spring Boot",
        "AWS Cloud",
        "Docker Kubernetes",
        "Machine Learning TensorFlow",
        "Angular TypeScript",
        "Ruby on Rails",
        "Go microservices",
        "React Native"
    ],
    
    "Multi-Skill Searches": [
        "Python Django PostgreSQL",
        "React Node.js MongoDB",
        "Java Spring AWS Docker",
        "Python Machine Learning AWS",
        "JavaScript React GraphQL",
        "Kubernetes Docker CI/CD",
        "Python Flask Redis",
        "Vue.js Laravel MySQL",
        "Android Kotlin Firebase",
        "iOS Swift CoreData"
    ],
    
    "Experience-Based Searches": [
        "Senior Python Developer with AWS",
        "Junior Frontend Developer React",
        "Lead DevOps Engineer Kubernetes",
        "Principal Software Engineer Java",
        "Entry Level Data Analyst Python",
        "Mid-level Full Stack Developer",
        "Senior Cloud Architect AWS Azure",
        "Staff Engineer distributed systems",
        "Engineering Manager Python team",
        "VP of Engineering startup experience"
    ],
    
    "Industry/Domain Searches": [
        "FinTech Python Developer",
        "Healthcare Data Scientist",
        "E-commerce Full Stack Engineer",
        "Gaming Backend Developer",
        "EdTech Mobile Developer",
        "SaaS DevOps Engineer",
        "Blockchain Developer Solidity",
        "IoT Engineer embedded systems",
        "AI/ML Engineer computer vision",
        "Security Engineer penetration testing"
    ],
    
    "Natural Language Queries": [
        "Find me a Python developer who knows AWS and has worked with microservices",
        "I need a React developer with 5+ years experience",
        "Looking for a DevOps engineer familiar with Kubernetes and Terraform",
        "Show me full stack developers who have worked at startups",
        "Find data scientists with PhD and machine learning experience",
        "Need a mobile developer who can work on both iOS and Android",
        "Looking for a senior engineer with team lead experience",
        "Find developers who know both Python and Go",
        "Show me engineers with cloud architecture experience",
        "Need someone who can handle both frontend and backend development"
    ],
    
    "Complex Skill Combinations": [
        "Python AWS Docker Kubernetes PostgreSQL Redis",
        "React TypeScript Node.js GraphQL MongoDB Docker",
        "Java Spring Boot Microservices Kafka AWS",
        "Python TensorFlow PyTorch Scikit-learn Pandas NumPy",
        "Angular .NET Core SQL Server Azure DevOps",
        "Vue.js Django PostgreSQL Redis Celery Docker",
        "React Native Firebase Redux TypeScript Jest",
        "Golang Kubernetes Prometheus Grafana CircleCI",
        "Ruby on Rails Sidekiq PostgreSQL Elasticsearch AWS",
        "PHP Laravel Vue.js MySQL Redis Docker"
    ]
}


async def run_search_examples(user_email: str = "promtitude@gmail.com", examples_per_category: int = 3):
    """Run vector search examples and display results."""
    
    async with async_session_maker() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.email == user_email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User {user_email} not found")
            return
        
        print(f"Running Vector Search Examples")
        print(f"User: {user.email}")
        print("=" * 80)
        
        for category, queries in SEARCH_EXAMPLES.items():
            print(f"\n\n{'='*80}")
            print(f"{category.upper()}")
            print("="*80)
            
            # Take first N examples from each category
            for query in queries[:examples_per_category]:
                print(f"\n🔍 Query: '{query}'")
                print("-" * 60)
                
                # Parse query to show what we're looking for
                parsed = query_parser.parse_query(query)
                if parsed['skills']:
                    print(f"   Skills: {', '.join(parsed['skills'])}")
                    if parsed.get('primary_skill'):
                        print(f"   Primary: {parsed['primary_skill']}")
                if parsed.get('seniority'):
                    print(f"   Seniority: {parsed['seniority']}")
                if parsed.get('roles'):
                    print(f"   Roles: {', '.join(parsed['roles'])}")
                
                # Perform search
                results = await search_service.search_resumes(
                    db,
                    query=query,
                    user_id=user.id,
                    limit=5
                )
                
                if results:
                    print(f"\n   Top {min(3, len(results))} Results:")
                    for i, (resume, score) in enumerate(results[:3], 1):
                        name = f"{resume['first_name']} {resume['last_name']}"
                        title = resume.get('current_title', 'N/A')
                        skills = resume.get('skills', [])[:5]
                        tier = resume.get('skill_tier', '?')
                        matched = resume.get('matched_skills', [])
                        
                        print(f"   {i}. {name} - {title}")
                        print(f"      Score: {score:.3f} | Tier: {tier}")
                        print(f"      Skills: {', '.join(skills)}{'...' if len(resume.get('skills', [])) > 5 else ''}")
                        if matched:
                            print(f"      Matched: {', '.join(matched)}")
                else:
                    print("   No results found")


async def test_specific_queries(user_email: str = "promtitude@gmail.com"):
    """Test specific queries to demonstrate the search capabilities."""
    
    test_queries = [
        # Primary skill examples
        ("Python Developer", "Should prioritize Python developers"),
        ("Python Developer with AWS", "Python developers should rank above AWS-only"),
        ("AWS Developer with Python", "AWS is primary here, Python secondary"),
        
        # Multi-skill examples
        ("Full Stack Python React AWS", "Looking for all three skills"),
        ("DevOps Docker Kubernetes Terraform", "DevOps toolchain"),
        
        # Natural language
        ("I need someone who knows Python and has experience with machine learning", "NLP query"),
        ("Find me a senior engineer with AWS and Python skills", "Conversational search"),
        
        # Experience + skills
        ("Senior Python Developer 5+ years", "Experience requirement"),
        ("Junior React Developer", "Entry level search"),
        
        # Domain specific
        ("FinTech Python Developer with Django", "Industry + skills"),
        ("Healthcare Data Scientist", "Domain specific role")
    ]
    
    async with async_session_maker() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.email == user_email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User {user_email} not found")
            return
        
        print(f"\nSpecific Query Tests")
        print("=" * 80)
        
        for query, description in test_queries:
            print(f"\n🔍 {description}")
            print(f"   Query: '{query}'")
            
            # Perform search
            results = await search_service.search_resumes(
                db,
                query=query,
                user_id=user.id,
                limit=3
            )
            
            if results:
                for i, (resume, score) in enumerate(results, 1):
                    name = f"{resume['first_name']} {resume['last_name']}"
                    tier = resume.get('skill_tier', '?')
                    matched = resume.get('matched_skills', [])
                    print(f"   {i}. {name} (Score: {score:.3f}, Tier: {tier}, Matched: {matched})")
            else:
                print("   No results")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run vector search examples")
    parser.add_argument("--user", default="promtitude@gmail.com", help="User email to search as")
    parser.add_argument("--examples", type=int, default=2, help="Examples per category")
    parser.add_argument("--specific", action="store_true", help="Run specific test queries")
    
    args = parser.parse_args()
    
    if args.specific:
        asyncio.run(test_specific_queries(args.user))
    else:
        asyncio.run(run_search_examples(args.user, args.examples))