#!/usr/bin/env python3
"""Generate 100 consistent test resumes for testing."""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Set seed for reproducibility
random.seed(42)

# Test data pools
FIRST_NAMES = [
    "John", "Sarah", "Michael", "Emily", "David", "Jessica", "James", "Jennifer", 
    "Robert", "Lisa", "William", "Mary", "Richard", "Patricia", "Thomas", "Linda",
    "Charles", "Barbara", "Joseph", "Elizabeth", "Christopher", "Susan", "Daniel", 
    "Margaret", "Matthew", "Dorothy", "Anthony", "Nancy", "Mark", "Karen",
    "Paul", "Betty", "Steven", "Helen", "Andrew", "Sandra", "Kenneth", "Donna",
    "Joshua", "Carol", "Kevin", "Ruth", "Brian", "Sharon", "George", "Michelle",
    "Edward", "Laura", "Ronald", "Sarah", "Timothy", "Kimberly", "Jason", "Deborah"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell"
]

LOCATIONS = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
    "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "San Francisco, CA",
    "Charlotte, NC", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC",
    "Boston, MA", "El Paso, TX", "Detroit, MI", "Nashville, TN", "Portland, OR",
    "Memphis, TN", "Oklahoma City, OK", "Las Vegas, NV", "Louisville, KY", "Baltimore, MD",
    "Milwaukee, WI", "Albuquerque, NM", "Tucson, AZ", "Fresno, CA", "Mesa, AZ",
    "Sacramento, CA", "Atlanta, GA", "Kansas City, MO", "Colorado Springs, CO", "Miami, FL"
]

# Technology skills pools
PROGRAMMING_LANGUAGES = [
    "Python", "JavaScript", "Java", "C++", "C#", "TypeScript", "Go", "Rust", "Ruby", "PHP",
    "Swift", "Kotlin", "Scala", "R", "MATLAB", "Perl", "Objective-C", "Dart", "Lua", "Julia"
]

FRAMEWORKS = [
    "React", "Angular", "Vue.js", "Django", "Flask", "Spring Boot", "Express.js", "Node.js",
    "ASP.NET", ".NET Core", "Ruby on Rails", "Laravel", "Symfony", "FastAPI", "Next.js",
    "Gatsby", "Nuxt.js", "Svelte", "Ember.js", "Backbone.js"
]

DATABASES = [
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "Oracle",
    "SQL Server", "DynamoDB", "Neo4j", "InfluxDB", "CouchDB", "MariaDB", "SQLite", "Firestore"
]

CLOUD_PLATFORMS = [
    "AWS", "Azure", "Google Cloud", "DigitalOcean", "Heroku", "IBM Cloud", "Oracle Cloud",
    "Alibaba Cloud", "Linode", "Vultr"
]

DEVOPS_TOOLS = [
    "Docker", "Kubernetes", "Jenkins", "GitLab CI", "GitHub Actions", "CircleCI", "Travis CI",
    "Terraform", "Ansible", "Puppet", "Chef", "Prometheus", "Grafana", "ELK Stack", "Datadog"
]

# Role-specific skill sets
ROLE_SKILLS = {
    "Frontend Developer": {
        "primary": ["JavaScript", "React", "HTML/CSS", "TypeScript"],
        "secondary": ["Vue.js", "Angular", "Webpack", "SASS", "Redux", "GraphQL"]
    },
    "Backend Developer": {
        "primary": ["Python", "Node.js", "PostgreSQL", "REST APIs"],
        "secondary": ["Django", "Express.js", "MongoDB", "Redis", "RabbitMQ", "Microservices"]
    },
    "Full Stack Developer": {
        "primary": ["JavaScript", "Python", "React", "Node.js", "PostgreSQL"],
        "secondary": ["Docker", "AWS", "TypeScript", "MongoDB", "GraphQL", "CI/CD"]
    },
    "DevOps Engineer": {
        "primary": ["Docker", "Kubernetes", "AWS", "Terraform"],
        "secondary": ["Jenkins", "Ansible", "Python", "Bash", "Monitoring", "Linux"]
    },
    "Data Engineer": {
        "primary": ["Python", "SQL", "Apache Spark", "AWS"],
        "secondary": ["Airflow", "Kafka", "Hadoop", "ETL", "Redshift", "Snowflake"]
    },
    "Data Scientist": {
        "primary": ["Python", "Machine Learning", "SQL", "Statistics"],
        "secondary": ["TensorFlow", "PyTorch", "R", "Pandas", "NumPy", "Scikit-learn"]
    },
    "Mobile Developer": {
        "primary": ["React Native", "Flutter", "Swift", "Kotlin"],
        "secondary": ["iOS", "Android", "Firebase", "REST APIs", "GraphQL", "Redux"]
    },
    "QA Engineer": {
        "primary": ["Selenium", "Python", "Test Automation", "API Testing"],
        "secondary": ["Cypress", "Jest", "JUnit", "Postman", "LoadRunner", "JIRA"]
    },
    "Security Engineer": {
        "primary": ["Python", "Security", "AWS", "Penetration Testing"],
        "secondary": ["OWASP", "Burp Suite", "Metasploit", "Cryptography", "Compliance", "Firewall"]
    },
    "Site Reliability Engineer": {
        "primary": ["Kubernetes", "Python", "AWS", "Monitoring"],
        "secondary": ["Prometheus", "Grafana", "Terraform", "Go", "Linux", "Incident Response"]
    }
}

def generate_email(first_name: str, last_name: str, index: int) -> str:
    """Generate consistent email."""
    return f"{first_name.lower()}.{last_name.lower()}{index}@example.com"

def generate_phone() -> str:
    """Generate consistent phone number."""
    area = random.randint(200, 999)
    prefix = random.randint(200, 999)
    line = random.randint(1000, 9999)
    return f"({area}) {prefix}-{line}"

def generate_skills_for_role(role: str) -> List[str]:
    """Generate consistent skills based on role."""
    if role in ROLE_SKILLS:
        skills = ROLE_SKILLS[role]["primary"].copy()
        # Add some secondary skills
        secondary = ROLE_SKILLS[role]["secondary"]
        num_secondary = random.randint(2, 4)
        skills.extend(random.sample(secondary, min(num_secondary, len(secondary))))
        
        # Add some general skills
        general_skills = ["Git", "Agile", "Communication", "Problem Solving", "Team Collaboration"]
        skills.extend(random.sample(general_skills, 2))
        
        return skills
    else:
        # Generic skill set
        return random.sample(PROGRAMMING_LANGUAGES, 3) + random.sample(FRAMEWORKS, 2) + ["Git", "Agile"]

def generate_summary(name: str, role: str, years: int, skills: List[str]) -> str:
    """Generate consistent professional summary."""
    skill_str = ", ".join(skills[:3])
    
    templates = [
        f"Experienced {role} with {years} years of expertise in {skill_str}. "
        f"Passionate about building scalable solutions and working in collaborative environments. "
        f"Strong problem-solving skills and commitment to code quality.",
        
        f"Results-driven {role} with {years}+ years of experience specializing in {skill_str}. "
        f"Proven track record of delivering high-quality software solutions on time. "
        f"Excellent communication skills and experience working in Agile teams.",
        
        f"Innovative {role} with {years} years of hands-on experience in {skill_str}. "
        f"Dedicated to continuous learning and staying current with industry best practices. "
        f"Strong analytical skills and attention to detail.",
        
        f"Senior {role} with {years}+ years building production applications using {skill_str}. "
        f"Experience leading technical initiatives and mentoring junior developers. "
        f"Focused on delivering business value through technology."
    ]
    
    return templates[hash(name) % len(templates)]

def generate_work_experience(role: str, years: int, skills: List[str]) -> List[Dict[str, Any]]:
    """Generate consistent work experience."""
    experiences = []
    remaining_years = years
    
    companies = [
        "Tech Innovations Inc", "Digital Solutions LLC", "Cloud Systems Corp",
        "Data Dynamics", "Software Craftsmen", "Agile Development Co",
        "Innovation Labs", "Future Tech Solutions", "Smart Systems Inc",
        "Global Software Partners"
    ]
    
    position_prefixes = ["Senior", "Lead", "Staff", "", "Junior"]
    
    while remaining_years > 0 and len(experiences) < 4:
        duration = min(random.randint(2, 5), remaining_years)
        
        if remaining_years == years:  # Current position
            title = f"{position_prefixes[min(len(experiences), 2)]} {role}".strip()
            current = True
        else:
            title = f"{position_prefixes[min(len(experiences) + 1, 4)]} {role}".strip()
            current = False
        
        experience = {
            "title": title,
            "company": random.choice(companies),
            "duration": f"{duration} years",
            "current": current,
            "description": f"Developed and maintained applications using {', '.join(random.sample(skills[:5], 3))}. "
                          f"Collaborated with cross-functional teams to deliver high-quality software solutions."
        }
        
        experiences.append(experience)
        remaining_years -= duration
    
    return experiences

def generate_education() -> List[Dict[str, str]]:
    """Generate consistent education."""
    universities = [
        "State University", "Tech Institute", "University of Technology",
        "Engineering College", "Computer Science University"
    ]
    
    degrees = [
        "Bachelor of Science in Computer Science",
        "Bachelor of Engineering in Software Engineering",
        "Master of Science in Computer Science",
        "Bachelor of Science in Information Technology"
    ]
    
    education = [{
        "degree": random.choice(degrees),
        "institution": random.choice(universities),
        "year": str(random.randint(2005, 2020))
    }]
    
    return education

def generate_100_resumes() -> List[Dict[str, Any]]:
    """Generate 100 consistent test resumes."""
    resumes = []
    
    # Define the distribution of roles
    roles = list(ROLE_SKILLS.keys())
    
    # Special resumes for testing specific searches
    special_resumes = [
        # Resume 1: Perfect Python + AWS match
        {
            "first_name": "William",
            "last_name": "Alves",
            "role": "Backend Developer",
            "skills": ["Python", "AWS", "Django", "PostgreSQL", "Docker", "REST APIs", "Git", "Agile"],
            "years": 8
        },
        # Resume 2: Senior Python with multiple cloud platforms
        {
            "first_name": "Sarah",
            "last_name": "Chen",
            "role": "Full Stack Developer", 
            "skills": ["Python", "AWS", "Azure", "React", "Node.js", "MongoDB", "Kubernetes", "CI/CD"],
            "years": 10
        },
        # Resume 3: Python focus without AWS
        {
            "first_name": "Michael",
            "last_name": "Johnson",
            "role": "Data Scientist",
            "skills": ["Python", "Machine Learning", "TensorFlow", "SQL", "Pandas", "NumPy", "Statistics"],
            "years": 6
        },
        # Resume 4: AWS focus without Python
        {
            "first_name": "Emily",
            "last_name": "Williams",
            "role": "DevOps Engineer",
            "skills": ["AWS", "Terraform", "Docker", "Kubernetes", "Jenkins", "Bash", "Monitoring"],
            "years": 7
        },
        # Resume 5: Junior Python developer
        {
            "first_name": "David",
            "last_name": "Brown",
            "role": "Backend Developer",
            "skills": ["Python", "Flask", "MySQL", "Git", "Linux", "REST APIs"],
            "years": 2
        }
    ]
    
    # Generate special resumes first
    for i, special in enumerate(special_resumes):
        email = generate_email(special["first_name"], special["last_name"], i + 1)
        phone = generate_phone()
        location = LOCATIONS[i % len(LOCATIONS)]
        
        summary = generate_summary(
            f"{special['first_name']} {special['last_name']}", 
            special["role"], 
            special["years"], 
            special["skills"]
        )
        
        resume = {
            "first_name": special["first_name"],
            "last_name": special["last_name"],
            "email": email,
            "phone": phone,
            "location": location,
            "current_title": special["role"],
            "years_experience": special["years"],
            "skills": special["skills"],
            "summary": summary,
            "work_experience": generate_work_experience(special["role"], special["years"], special["skills"]),
            "education": generate_education()
        }
        
        resumes.append(resume)
    
    # Generate remaining 95 resumes
    for i in range(5, 100):
        first_name = FIRST_NAMES[i % len(FIRST_NAMES)]
        last_name = LAST_NAMES[i % len(LAST_NAMES)]
        role = roles[i % len(roles)]
        
        # Vary experience levels
        if i < 20:
            years = random.randint(1, 3)  # Junior
        elif i < 60:
            years = random.randint(4, 8)  # Mid-level
        else:
            years = random.randint(9, 15)  # Senior
        
        email = generate_email(first_name, last_name, i + 1)
        phone = generate_phone()
        location = LOCATIONS[i % len(LOCATIONS)]
        
        skills = generate_skills_for_role(role)
        
        # Add some variety - 20% chance to add Python or AWS
        if random.random() < 0.2:
            skills.append("Python")
        if random.random() < 0.2:
            skills.append("AWS")
        
        # Remove duplicates
        skills = list(dict.fromkeys(skills))
        
        summary = generate_summary(f"{first_name} {last_name}", role, years, skills)
        
        resume = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "location": location,
            "current_title": role,
            "years_experience": years,
            "skills": skills,
            "summary": summary,
            "work_experience": generate_work_experience(role, years, skills),
            "education": generate_education()
        }
        
        resumes.append(resume)
    
    return resumes

def save_resumes_to_file(resumes: List[Dict[str, Any]], filename: str):
    """Save resumes to JSON file."""
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_count": len(resumes),
        "test_user_email": "promtitude@gmail.com",
        "resumes": resumes
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(resumes)} resumes to {filename}")

def create_upload_instructions():
    """Create instructions for uploading resumes."""
    instructions = """
# Test Resume Upload Instructions

## Files Generated:
1. `test_resumes_100.json` - Full resume data for upload
2. `test_resumes_names_only.txt` - Simple list of names for quick reference

## How to Upload to Production:

### Option 1: Using the Web Interface
1. Go to your Promtitude dashboard
2. Navigate to Resume Management or Bulk Import
3. Upload the `test_resumes_100.json` file
4. Select user: promtitude@gmail.com
5. Click Import

### Option 2: Using API (if available)
```bash
curl -X POST https://your-domain.com/api/v1/resumes/bulk-import \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @test_resumes_100.json
```

### Option 3: Direct Database Script
1. Copy `test_resumes_100.json` to your backend folder
2. Run: `python scripts/import_test_resumes.py`

## Special Test Cases:
- **William Alves** - Perfect Python + AWS match
- **Sarah Chen** - Senior Python with AWS, Azure
- **Michael Johnson** - Python without AWS
- **Emily Williams** - AWS without Python
- **David Brown** - Junior Python developer

## Search Queries to Test:
1. "Senior Python developer with AWS" - Should rank William Alves and Sarah Chen highest
2. "Python" - Should return all Python developers
3. "AWS" - Should return all AWS professionals
4. "DevOps" - Should return DevOps engineers
5. "Machine Learning" - Should return data scientists

## Verification:
After upload, verify with:
- Total count should be 100
- Search for "William Alves" should return 1 result
- All resumes should be associated with promtitude@gmail.com
"""
    
    with open('test_resume_upload_instructions.md', 'w') as f:
        f.write(instructions)
    
    print("✅ Created upload instructions in test_resume_upload_instructions.md")

def create_name_list(resumes: List[Dict[str, Any]]):
    """Create a simple text file with just names for reference."""
    with open('test_resumes_names_only.txt', 'w') as f:
        f.write("Test Resume Names (100 total)\n")
        f.write("=" * 40 + "\n\n")
        
        for i, resume in enumerate(resumes):
            f.write(f"{i+1:3d}. {resume['first_name']} {resume['last_name']} - {resume['current_title']}\n")
    
    print("✅ Created name list in test_resumes_names_only.txt")

def main():
    """Generate test resumes."""
    print("Generating 100 test resumes...")
    print("=" * 60)
    
    # Generate resumes
    resumes = generate_100_resumes()
    
    # Save to JSON file
    save_resumes_to_file(resumes, 'test_resumes_100.json')
    
    # Create name list
    create_name_list(resumes)
    
    # Create upload instructions
    create_upload_instructions()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"- Generated {len(resumes)} test resumes")
    print("- Special test cases for Python/AWS searches included")
    print("- Files created:")
    print("  - test_resumes_100.json (main data file)")
    print("  - test_resumes_names_only.txt (quick reference)")
    print("  - test_resume_upload_instructions.md (how to upload)")
    print("\nUse these same files for both local and production testing!")

if __name__ == "__main__":
    main()