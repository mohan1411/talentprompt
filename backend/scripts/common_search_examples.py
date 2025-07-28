#!/usr/bin/env python3
"""Common vector search examples with expected results."""

# Common search queries you can use to test the vector search functionality

COMMON_SEARCHES = {
    "Basic Skill Searches": [
        "Python",                          # Find all Python developers
        "JavaScript",                      # Find all JavaScript developers
        "AWS",                            # Find all AWS engineers
        "Docker",                         # Find all Docker users
        "React",                          # Find all React developers
    ],
    
    "Role + Skill Combinations": [
        "Python Developer",                # Python is the primary skill
        "React Developer",                 # React is the primary skill
        "DevOps Engineer",                 # Role-based search
        "Full Stack Developer",            # General full stack search
        "Data Scientist",                  # Role-based search
    ],
    
    "Multi-Skill Searches": [
        "Python AWS",                      # Python primary, AWS secondary
        "React Node.js",                   # React primary, Node.js secondary
        "Java Spring Boot",                # Java primary, Spring Boot secondary
        "Docker Kubernetes",               # Docker primary, Kubernetes secondary
        "Python Django REST",              # Python primary, Django and REST secondary
    ],
    
    "Seniority + Skills": [
        "Senior Python Developer",         # Senior level Python
        "Junior React Developer",          # Entry level React
        "Lead DevOps Engineer",           # Leadership role
        "Principal Software Engineer",     # Very senior role
        "Mid-level Full Stack Developer",  # Mid-level general
    ],
    
    "Complex Queries": [
        "Senior Python Developer with AWS experience",
        "Full Stack Engineer React Node.js MongoDB",
        "DevOps Engineer with Kubernetes and Terraform",
        "Data Scientist with Machine Learning and Python",
        "Mobile Developer React Native iOS Android",
    ],
    
    "Natural Language Queries": [
        "Find me a Python developer who knows cloud technologies",
        "I need someone with React and backend experience",
        "Looking for a DevOps engineer with AWS skills",
        "Show me developers with both Python and JavaScript",
        "Need a data scientist with machine learning experience",
    ]
}

# How the search ranking works:

print("""
VECTOR SEARCH EXAMPLES AND RANKING SYSTEM
=========================================

The enhanced search uses a 5-tier ranking system:

TIER 1 (Score: ~1.0+) - Perfect Match
  - Has ALL required skills
  - Example: Search "Python AWS" → Candidate has both Python AND AWS

TIER 2 (Score: ~0.6-0.8) - Primary + Secondary
  - Has primary skill + most secondary skills (75%+ match)
  - Example: Search "Python Django REST AWS" → Has Python + Django + REST (missing AWS)

TIER 3 (Score: ~0.4-0.5) - Primary Only
  - Has the primary/main skill but missing secondary skills
  - Example: Search "Python AWS" → Has Python but not AWS

TIER 4 (Score: ~0.15-0.2) - Secondary Only
  - Missing primary skill but has some secondary skills
  - Example: Search "Python AWS" → Has AWS but not Python

TIER 5 (Score: ~0.05) - No Match
  - Has none of the required skills
  - Example: Search "Python AWS" → Has neither Python nor AWS

PRIMARY SKILL IDENTIFICATION:
- First skill mentioned is usually primary
- Or skill that appears in the role (e.g., "Python Developer" → Python is primary)
- Primary skill has 50% weight in scoring

EXAMPLE SEARCHES TO TRY:
""")

for category, searches in COMMON_SEARCHES.items():
    print(f"\n{category}:")
    for search in searches:
        print(f"  - {search}")

print("""
TESTING THE SEARCH:
1. Use the search endpoint: POST /api/v1/search/
2. Include the query in the request body
3. Results will include tier and skill match information

CURL EXAMPLE:
curl -X POST http://localhost:8001/api/v1/search/ \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{
    "query": "Senior Python Developer with AWS",
    "limit": 10
  }'
""")