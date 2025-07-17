"""Enhanced skill search functionality to handle case variations and partial matches."""

import re
from typing import List, Set
from sqlalchemy import or_, func, String, text
from sqlalchemy.sql.expression import cast

def create_skill_search_conditions(skill_query: str, resume_model):
    """Create search conditions for skills that handle case variations and common formats.
    
    Args:
        skill_query: The skill to search for (e.g., "WebSphere", "websphere", "web sphere")
        resume_model: The Resume SQLAlchemy model
        
    Returns:
        List of SQLAlchemy conditions to use with OR
    """
    conditions = []
    
    # Normalize the skill query
    skill_lower = skill_query.lower()
    skill_title = skill_query.title()
    skill_upper = skill_query.upper()
    
    # Handle camelCase/PascalCase by adding spaces
    # "WebSphere" -> "Web Sphere"
    skill_spaced = re.sub(r'(?<!^)(?=[A-Z])', ' ', skill_query).strip()
    skill_spaced_lower = skill_spaced.lower()
    
    # Common variations to check
    variations = [
        skill_query,  # Original
        skill_lower,  # lowercase
        skill_title,  # Title Case
        skill_upper,  # UPPERCASE
        skill_spaced,  # With spaces
        skill_spaced_lower,  # with spaces lowercase
    ]
    
    # Remove duplicates
    variations = list(set(variations))
    
    # Check skills JSON array for each variation
    for variation in variations:
        # Exact match in JSON array
        conditions.append(
            cast(resume_model.skills, String).ilike(f'%"{variation}"%')
        )
        
        # Match with common suffixes/prefixes
        for suffix in ['', ' Developer', ' Engineer', ' Expert', ' Specialist']:
            if suffix and not variation.endswith(suffix.lower()):
                conditions.append(
                    cast(resume_model.skills, String).ilike(f'%"{variation}{suffix}"%')
                )
    
    # Also check in raw text and summary for broader matching
    for field in [resume_model.raw_text, resume_model.summary, resume_model.current_title]:
        if field is not None:
            conditions.append(field.ilike(f'%{skill_query}%'))
            conditions.append(field.ilike(f'%{skill_spaced}%'))
    
    # PostgreSQL specific: Use JSON operators for more precise matching
    # This checks if any element in the skills array contains the search term
    conditions.append(
        text(f"""
        EXISTS (
            SELECT 1 FROM jsonb_array_elements_text(skills::jsonb) AS skill
            WHERE skill ILIKE '%{skill_query}%'
        )
        """)
    )
    
    return conditions


def normalize_skill_for_storage(skill: str) -> str:
    """Normalize skill names for consistent storage.
    
    Args:
        skill: Raw skill name
        
    Returns:
        Normalized skill name
    """
    # Common corrections
    skill_corrections = {
        'websphere': 'WebSphere',
        'web sphere': 'WebSphere',
        'websphere message broker': 'WebSphere Message Broker',
        'web sphere message broker': 'WebSphere Message Broker',
        'javascript': 'JavaScript',
        'java script': 'JavaScript',
        'nodejs': 'Node.js',
        'node js': 'Node.js',
        'reactjs': 'React.js',
        'react js': 'React.js',
        'vuejs': 'Vue.js',
        'vue js': 'Vue.js',
        'angular js': 'AngularJS',
        'angularjs': 'AngularJS',
        'asp.net': 'ASP.NET',
        'asp net': 'ASP.NET',
        '.net': '.NET',
        'dot net': '.NET',
        'c#': 'C#',
        'c sharp': 'C#',
        'c++': 'C++',
        'c plus plus': 'C++',
    }
    
    # Check for exact match in corrections
    skill_lower = skill.lower().strip()
    if skill_lower in skill_corrections:
        return skill_corrections[skill_lower]
    
    # Otherwise, preserve original casing but clean up
    return skill.strip()


def extract_skills_from_text(text: str) -> List[str]:
    """Extract skills from free text with better WebSphere detection.
    
    Args:
        text: Raw text to extract skills from
        
    Returns:
        List of normalized skill names
    """
    if not text:
        return []
    
    skills = set()
    
    # Common technology patterns with proper casing
    tech_patterns = [
        # IBM Technologies
        (r'\b(?:WebSphere|Websphere|web\s*sphere)\b', 'WebSphere'),
        (r'\b(?:WebSphere\s+Message\s+Broker|Websphere\s+message\s+broker|WMB)\b', 'WebSphere Message Broker'),
        (r'\b(?:WebSphere\s+MQ|Websphere\s+mq|IBM\s+MQ)\b', 'WebSphere MQ'),
        (r'\b(?:WebSphere\s+Application\s+Server|WAS)\b', 'WebSphere Application Server'),
        
        # Other common technologies
        (r'\b(?:JavaScript|Javascript|javascript|JS)\b', 'JavaScript'),
        (r'\b(?:Node\.?js|NodeJS|node\.?js)\b', 'Node.js'),
        (r'\b(?:React\.?js|ReactJS|react\.?js|React)\b', 'React.js'),
        (r'\b(?:Vue\.?js|VueJS|vue\.?js|Vue)\b', 'Vue.js'),
        (r'\b(?:Angular\.?js|AngularJS|angular\.?js)\b', 'AngularJS'),
        (r'\b(?:ASP\.NET|ASP\.Net|asp\.net)\b', 'ASP.NET'),
        (r'\b(?:\.NET|\.Net|dot\s*net|DotNet)\b', '.NET'),
        (r'\b(?:C\#|C\s+Sharp|c\s+sharp)\b', 'C#'),
        (r'\b(?:C\+\+|C\s+Plus\s+Plus|cpp)\b', 'C++'),
    ]
    
    # Apply patterns
    for pattern, normalized in tech_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            skills.add(normalized)
    
    # Also extract other common skills
    common_skills = re.findall(
        r'\b(?:Python|Java|SQL|Docker|Kubernetes|AWS|Azure|GCP|'
        r'MongoDB|PostgreSQL|MySQL|Redis|Elasticsearch|'
        r'Spring|Django|Flask|Express|Laravel|'
        r'Git|Jenkins|Terraform|Ansible|'
        r'Machine Learning|Deep Learning|Data Science|'
        r'REST|GraphQL|Microservices|DevOps|CI/CD|'
        r'HTML|CSS|TypeScript|Go|Rust|Ruby|PHP|Swift|Kotlin|'
        r'Linux|Windows|Unix|Agile|Scrum)\b',
        text,
        re.IGNORECASE
    )
    
    for skill in common_skills:
        skills.add(normalize_skill_for_storage(skill))
    
    return list(skills)


def enhance_search_query_for_skills(query: str) -> List[str]:
    """Enhance search query to handle skill variations.
    
    Args:
        query: Original search query
        
    Returns:
        List of query variations to search for
    """
    queries = [query]  # Original query
    
    # Handle common variations
    query_lower = query.lower()
    
    # WebSphere specific variations
    if 'websphere' in query_lower:
        queries.extend([
            'WebSphere',
            'websphere',
            'web sphere',
            'Web Sphere',
            'IBM WebSphere'
        ])
        
        if 'message' in query_lower and 'broker' in query_lower:
            queries.extend([
                'WebSphere Message Broker',
                'WMB',
                'IBM Integration Bus',
                'IIB'
            ])
        elif 'mq' in query_lower:
            queries.extend([
                'WebSphere MQ',
                'IBM MQ',
                'MQ Series'
            ])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)
    
    return unique_queries