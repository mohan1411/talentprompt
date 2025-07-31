#!/usr/bin/env python3
"""Test Mind Reader Search query analysis."""

import requests
import json

def test_mind_reader_search():
    """Test the Mind Reader Search with various queries."""
    
    # Test queries that should show skills
    test_queries = [
        "Python Developers with AWS",
        "Senior Django developer with EC2 experience",
        "React and TypeScript frontend engineer",
        "DevOps engineer with Kubernetes and Docker",
        "Machine learning engineer with TensorFlow"
    ]
    
    # Login first to get token
    print("Logging in...")
    # Use form data for OAuth2PasswordRequestForm
    form_data = {
        "username": "admin@example.com",
        "password": "CorrectAdminPassword123!"
    }
    login_response = requests.post(
        "http://localhost:8001/api/v1/auth/login",
        data=form_data
    )
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nTesting Mind Reader Search query analysis...")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: \"{query}\"")
        print("-" * 40)
        
        # Test the progressive search endpoint
        response = requests.get(
            f"http://localhost:8001/api/v1/search/progressive",
            params={"query": query, "limit": 5, "token": token},
            stream=True
        )
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            continue
        
        # Process the SSE stream
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    try:
                        data = json.loads(decoded_line[6:])
                        
                        # We're interested in the parsed_query from the first stage
                        if data.get('stage') == 'instant' and 'parsed_query' in data:
                            parsed = data['parsed_query']
                            print(f"  Primary Skills: {parsed.get('primary_skills', [])}")
                            print(f"  Secondary Skills: {parsed.get('secondary_skills', [])}")
                            print(f"  Implied Skills: {parsed.get('implied_skills', [])}")
                            print(f"  Experience Level: {parsed.get('experience_level', 'any')}")
                            print(f"  Role Type: {parsed.get('role_type', 'any')}")
                            print(f"  Search Intent: {parsed.get('search_intent', 'general')}")
                            if parsed.get('corrected_query'):
                                print(f"  Corrected Query: {parsed['corrected_query']}")
                            break
                    except json.JSONDecodeError:
                        pass

if __name__ == "__main__":
    test_mind_reader_search()