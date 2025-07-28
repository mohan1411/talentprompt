#!/usr/bin/env python3
"""Generate test resumes for vector search testing."""

import asyncio
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User
from app.models.resume import Resume
from app.services.reindex_service import reindex_service

# Test data pools
FIRST_NAMES = [
    "John", "Jane", "Michael", "Sarah", "David", "Emma", "Robert", "Lisa",
    "James", "Maria", "William", "Jennifer", "Richard", "Patricia", "Charles",
    "Linda", "Joseph", "Barbara", "Thomas", "Elizabeth", "Christopher", "Susan",
    "Daniel", "Jessica", "Matthew", "Karen", "Anthony", "Nancy", "Mark", "Betty",
    "Raj", "Priya", "Amit", "Neha", "Vikram", "Anjali", "Arjun", "Kavya",
    "Chen", "Wei", "Li", "Xiaoming", "Zhang", "Ling", "Wang", "Hui",
    "Carlos", "Ana", "Luis", "Sofia", "Diego", "Valentina", "Alejandro", "Isabella"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Patel", "Kumar", "Sharma", "Singh", "Gupta", "Shah", "Mehta", "Verma",
    "Chen", "Li", "Wang", "Zhang", "Liu", "Huang", "Wu", "Zhou",
    "Silva", "Santos", "Oliveira", "Souza", "Costa", "Ferreira", "Alves", "Ribeiro"
]

TECH_SKILLS = {
    "languages": ["Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R"],
    "frontend": ["React", "Angular", "Vue.js", "Next.js", "Svelte", "HTML5", "CSS3", "Sass", "Redux", "MobX", "Webpack", "Tailwind CSS"],
    "backend": ["Node.js", "Django", "Flask", "FastAPI", "Spring Boot", "Express.js", "Ruby on Rails", ".NET Core", "Laravel", "NestJS"],
    "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "DynamoDB", "Oracle", "SQL Server", "Neo4j"],
    "cloud": ["AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Terraform", "Jenkins", "GitLab CI", "CircleCI", "Ansible"],
    "data": ["TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Spark", "Hadoop", "Kafka", "Airflow", "Tableau"],
    "mobile": ["React Native", "Flutter", "iOS", "Android", "Xamarin", "Ionic", "Swift", "Kotlin", "Objective-C"],
    "tools": ["Git", "JIRA", "Confluence", "Slack", "VS Code", "IntelliJ", "Postman", "GraphQL", "REST APIs", "Microservices"]
}

JOB_TITLES = [
    "Software Engineer", "Senior Software Engineer", "Lead Software Engineer", "Principal Engineer",
    "Full Stack Developer", "Frontend Developer", "Backend Developer", "DevOps Engineer",
    "Data Scientist", "Machine Learning Engineer", "Data Engineer", "AI Researcher",
    "Mobile Developer", "iOS Developer", "Android Developer", "React Native Developer",
    "Cloud Architect", "Solutions Architect", "Site Reliability Engineer", "Platform Engineer",
    "Technical Lead", "Engineering Manager", "Staff Engineer", "Software Architect",
    "QA Engineer", "Test Automation Engineer", "Security Engineer", "Database Administrator"
]

COMPANIES = [
    "TechCorp", "DataSystems Inc", "CloudNet Solutions", "InnovateTech", "Digital Dynamics",
    "CyberCore", "WebWorks", "AppForge", "CodeCraft", "ByteBuilder", "PixelPerfect",
    "AlgoExperts", "SmartSoft", "FutureTech", "QuantumLeap", "NexGen Systems",
    "TechPioneers", "CodeMasters", "DataDriven Co", "CloudFirst", "AI Innovations",
    "MobileTech", "SecureNet", "DevOps Pro", "Agile Solutions", "Tech Innovators"
]

LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Boston, MA",
    "Los Angeles, CA", "Chicago, IL", "Denver, CO", "Portland, OR", "San Diego, CA",
    "London, UK", "Berlin, Germany", "Paris, France", "Amsterdam, Netherlands", "Dublin, Ireland",
    "Toronto, Canada", "Vancouver, Canada", "Sydney, Australia", "Melbourne, Australia",
    "Singapore", "Tokyo, Japan", "Bangalore, India", "Mumbai, India", "Delhi, India",
    "Shanghai, China", "Beijing, China", "Hong Kong", "Dubai, UAE", "Tel Aviv, Israel"
]

SUMMARY_TEMPLATES = [
    "Experienced {title} with {years} years of expertise in {skill1}, {skill2}, and {skill3}. Passionate about building scalable solutions and leading technical initiatives.",
    "Results-driven {title} specializing in {skill1} and {skill2}. {years} years of experience delivering high-quality software solutions in fast-paced environments.",
    "Innovative {title} with strong background in {skill1}, {skill2}, and {skill3}. Proven track record of {years} years in developing cutting-edge applications.",
    "Dedicated {title} with {years} years of hands-on experience in {skill1} and {skill2}. Committed to continuous learning and staying current with industry trends.",
    "Strategic {title} bringing {years} years of expertise in {skill1}, {skill2}, and {skill3}. Known for problem-solving abilities and delivering projects on time.",
    "Versatile {title} with {years} years in software development. Expert in {skill1} and {skill2}, with additional experience in {skill3}.",
    "Accomplished {title} with a {years}-year track record in {skill1} and {skill2}. Skilled at architecting robust solutions and mentoring junior developers.",
    "Dynamic {title} offering {years} years of experience in {skill1}, {skill2}, and {skill3}. Passionate about clean code and agile methodologies."
]


def generate_email(first_name: str, last_name: str) -> str:
    """Generate a realistic email address."""
    domains = ["gmail.com", "yahoo.com", "outlook.com", "example.com", "techmail.com"]
    formats = [
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name[0].lower()}{last_name.lower()}",
        f"{first_name.lower()}.{last_name[0].lower()}",
        f"{first_name.lower()}{random.randint(1, 99)}"
    ]
    return f"{random.choice(formats)}@{random.choice(domains)}"


def generate_phone() -> str:
    """Generate a realistic phone number."""
    return f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"


def generate_linkedin_url(first_name: str, last_name: str) -> str:
    """Generate a unique LinkedIn URL."""
    # Add random string to ensure uniqueness
    unique_id = str(uuid4())[:8]
    return f"https://www.linkedin.com/in/{first_name.lower()}-{last_name.lower()}-{unique_id}"


def select_skills(years_exp: int, force_combinations: bool = True) -> List[str]:
    """Select appropriate skills based on experience level.
    
    Args:
        years_exp: Years of experience
        force_combinations: If True, ensures some common skill combinations exist
    """
    skill_count = min(5 + years_exp // 2, 15)  # More skills with more experience
    
    selected_skills = []
    
    # Common skill combinations to ensure realistic matches
    skill_combinations = [
        ["Python", "AWS", "Docker", "PostgreSQL"],
        ["Python", "AWS", "Django", "Redis"],
        ["JavaScript", "React", "Node.js", "MongoDB"],
        ["Java", "Spring Boot", "AWS", "MySQL"],
        ["Python", "Machine Learning", "TensorFlow", "AWS"],
        ["Python", "FastAPI", "PostgreSQL", "Docker"],
        ["TypeScript", "React", "Node.js", "GraphQL"],
        ["Go", "Kubernetes", "Docker", "AWS"],
        ["Python", "Data Science", "Pandas", "NumPy"],
        ["Java", "Microservices", "Kubernetes", "AWS"]
    ]
    
    # 30% chance to use a predefined combination as base
    if force_combinations and random.random() < 0.3:
        base_skills = random.choice(skill_combinations)
        selected_skills.extend(base_skills)
    
    # Ensure variety by selecting from different categories
    categories = list(TECH_SKILLS.keys())
    primary_category = random.choice(categories)
    
    # Add more skills from primary category
    remaining_slots = skill_count - len(selected_skills)
    if remaining_slots > 0:
        primary_skills = [s for s in TECH_SKILLS[primary_category] if s not in selected_skills]
        additional_primary = random.sample(primary_skills, 
                                         min(len(primary_skills), remaining_slots // 2))
        selected_skills.extend(additional_primary)
    
    # Add skills from other categories
    for category in categories:
        if category != primary_category and len(selected_skills) < skill_count:
            available = [s for s in TECH_SKILLS[category] if s not in selected_skills]
            if available:
                additional = random.sample(available, 
                                         min(len(available), 2))
                selected_skills.extend(additional)
    
    # Ensure specific combinations for testing
    # 10% chance to explicitly have Python + AWS
    if random.random() < 0.1 and "Python" not in selected_skills and "AWS" not in selected_skills:
        selected_skills.extend(["Python", "AWS"])
    
    return list(set(selected_skills))[:skill_count]


def generate_summary(title: str, years: int, skills: List[str]) -> str:
    """Generate a professional summary."""
    template = random.choice(SUMMARY_TEMPLATES)
    skill_sample = random.sample(skills, min(3, len(skills)))
    
    summary = template.format(
        title=title,
        years=years,
        skill1=skill_sample[0] if len(skill_sample) > 0 else "software development",
        skill2=skill_sample[1] if len(skill_sample) > 1 else "problem solving",
        skill3=skill_sample[2] if len(skill_sample) > 2 else "team collaboration"
    )
    
    return summary


def generate_resume_data(index: int) -> Dict[str, Any]:
    """Generate a single resume with realistic data."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    # Years of experience (weighted towards mid-level)
    years_exp = random.choices(
        range(1, 21),
        weights=[5, 8, 10, 12, 15, 15, 12, 10, 8, 5, 4, 3, 3, 2, 2, 1, 1, 1, 1, 1],
        k=1
    )[0]
    
    # Select title based on experience
    if years_exp < 3:
        title_pool = [t for t in JOB_TITLES if "Senior" not in t and "Lead" not in t and "Principal" not in t]
    elif years_exp < 7:
        title_pool = [t for t in JOB_TITLES if "Principal" not in t and "Staff" not in t]
    else:
        title_pool = JOB_TITLES
    
    title = random.choice(title_pool)
    
    # For the first 10 resumes, ensure we have some Senior Python Developers with AWS
    if index < 10 and index % 3 == 0:
        title = "Senior Software Engineer"
        years_exp = random.randint(7, 15)
    
    company = random.choice(COMPANIES)
    skills = select_skills(years_exp)
    
    # Ensure first few resumes have Python + AWS combination
    if index < 5:
        if "Python" not in skills:
            skills.append("Python")
        if "AWS" not in skills:
            skills.append("AWS")
        # Also add related skills
        if "Docker" not in skills and random.random() < 0.5:
            skills.append("Docker")
    
    # Include company in title for context
    full_title = f"{title} at {company}"
    
    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": generate_email(first_name, last_name),
        "phone": generate_phone(),
        "location": random.choice(LOCATIONS),
        "current_title": full_title,
        "summary": generate_summary(title, years_exp, skills),
        "years_experience": years_exp,
        "skills": skills,
        "keywords": random.sample(skills, min(5, len(skills))),  # Keywords are subset of skills
        "linkedin_url": generate_linkedin_url(first_name, last_name),
        "status": "active",
        "parse_status": "completed",
        "parsed_at": datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))
    }


async def create_test_resumes(count: int = 100) -> None:
    """Create test resumes for promtitude@gmail.com user."""
    # Create database engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=5
    )
    
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as db:
        try:
            # Find promtitude@gmail.com user
            stmt = select(User).where(User.email == "promtitude@gmail.com")
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ User promtitude@gmail.com not found!")
                return
            
            print(f"✓ Found user: {user.email} (ID: {user.id})")
            print(f"\nGenerating {count} test resumes...")
            
            # Generate and create resumes
            created_count = 0
            resumes_to_index = []
            
            for i in range(count):
                try:
                    # Generate resume data
                    resume_data = generate_resume_data(i)
                    
                    # Create resume object
                    resume = Resume(
                        user_id=user.id,
                        **resume_data
                    )
                    
                    db.add(resume)
                    
                    # Batch commit every 10 resumes
                    if (i + 1) % 10 == 0:
                        await db.flush()
                        print(f"  Created {i + 1}/{count} resumes...")
                    
                    resumes_to_index.append(resume)
                    created_count += 1
                    
                except Exception as e:
                    print(f"  ❌ Error creating resume {i + 1}: {e}")
            
            # Final commit
            await db.commit()
            print(f"\n✅ Successfully created {created_count} resumes in PostgreSQL")
            
            # Now index all resumes in vector search
            print("\nIndexing resumes in vector search...")
            indexed_count = 0
            
            for i, resume in enumerate(resumes_to_index):
                try:
                    success = await reindex_service.reindex_resume(db, resume)
                    if success:
                        indexed_count += 1
                    
                    if (i + 1) % 10 == 0:
                        print(f"  Indexed {i + 1}/{len(resumes_to_index)} resumes...")
                        
                except Exception as e:
                    print(f"  ❌ Error indexing resume {resume.id}: {e}")
            
            print(f"\n✅ Successfully indexed {indexed_count} resumes in Qdrant")
            
            # Summary
            print("\n" + "="*50)
            print("SUMMARY")
            print("="*50)
            print(f"User: {user.email}")
            print(f"Resumes created: {created_count}")
            print(f"Resumes indexed: {indexed_count}")
            
            if indexed_count < created_count:
                print(f"\n⚠️  Warning: {created_count - indexed_count} resumes failed to index")
                print("You may need to run the reindex script to fix this")
            
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            raise
        finally:
            await engine.dispose()


async def main():
    """Main function."""
    print("="*60)
    print("TEST RESUME GENERATOR")
    print("="*60)
    print("\nThis script will create 100 test resumes for promtitude@gmail.com")
    print("Each resume will have:")
    print("  - Realistic names and contact info")
    print("  - Diverse skills and experience levels")
    print("  - Professional summaries")
    print("  - Automatic vector indexing")
    
    await create_test_resumes(100)
    
    print("\n✅ Test resume generation complete!")
    print("\nNext steps:")
    print("1. Run the verification script to check indexing")
    print("2. Test vector search with various queries")
    print("3. Monitor search performance and relevance")


if __name__ == "__main__":
    asyncio.run(main())