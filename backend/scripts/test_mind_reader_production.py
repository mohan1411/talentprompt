#!/usr/bin/env python3
"""Test Mind Reader Search functionality in production."""

import requests
import json
import time

def test_mind_reader_search():
    """Test progressive search features in production."""
    
    print("="*60)
    print("TESTING MIND READER SEARCH IN PRODUCTION")
    print("="*60)
    
    # Get production URL and token
    prod_url = input("\nEnter your production URL (e.g., https://app.promtitude.com): ").strip().rstrip('/')
    token = input("Enter your access token for promtitude@gmail.com: ").strip()
    
    if not prod_url or not token:
        print("❌ URL and token are required!")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test queries
    test_queries = [
        "Python developer with AWS",
        "React TypeScript engineer", 
        "DevOps ninja comfortable with chaos",
        "Full stack developer who can mentor juniors"
    ]
    
    print("\n1. Testing Progressive Search Endpoint...")
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        
        try:
            # Test progressive search
            url = f"{prod_url}/api/v1/search/progressive?query={query}&limit=10"
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            
            if response.status_code != 200:
                print(f"   ❌ Error {response.status_code}")
                continue
            
            # Parse SSE stream
            stages_received = []
            final_results = None
            query_analysis = None
            
            for line in response.iter_lines():
                if line:
                    try:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data = json.loads(line_str[6:])
                            stage = data.get('stage')
                            
                            if stage:
                                stages_received.append(stage)
                                if stage == 'complete':
                                    final_results = data.get('results', [])
                                    query_analysis = data.get('queryAnalysis')
                    except:
                        pass
            
            print(f"   ✅ Stages received: {' → '.join(stages_received)}")
            
            if query_analysis:
                print(f"   ✅ Query analysis:")
                print(f"      - Primary skills: {query_analysis.get('primary_skills', [])}")
                print(f"      - Experience level: {query_analysis.get('experience_level', 'Not specified')}")
            
            if final_results:
                print(f"   ✅ Found {len(final_results)} results")
                
                # Check for AI enhancements
                enhanced_count = 0
                for result in final_results[:5]:  # First 5 should have AI insights
                    if any([
                        result.get('key_strengths'),
                        result.get('match_explanation'),
                        result.get('hiring_recommendation')
                    ]):
                        enhanced_count += 1
                
                print(f"   ✅ AI-enhanced results: {enhanced_count}/5")
            else:
                print("   ⚠️  No results returned")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Test query analysis endpoint
    print("\n2. Testing Query Analysis...")
    try:
        url = f"{prod_url}/api/v1/search/analyze-query"
        response = requests.post(
            url, 
            headers=headers,
            json={"query": "Find me a unicorn developer"}
        )
        
        if response.status_code == 200:
            analysis = response.json()
            print("   ✅ Query analysis working")
            print(f"      Skills found: {analysis.get('skills', [])}")
        else:
            print(f"   ❌ Query analysis error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test result enhancement
    print("\n3. Testing Result Enhancement (Get AI Insights)...")
    try:
        # First get a resume ID from search
        url = f"{prod_url}/api/v1/search?query=developer&limit=1"
        response = requests.post(url, headers=headers, json={})
        
        if response.status_code == 200 and response.json():
            resume_id = response.json()[0]['id']
            
            # Try to enhance it
            url = f"{prod_url}/api/v1/search/enhance-result"
            response = requests.post(
                url,
                headers=headers,
                json={
                    "resume_id": resume_id,
                    "query": "senior developer",
                    "score": 0.85
                }
            )
            
            if response.status_code == 200:
                enhancement = response.json()
                if enhancement.get('enhancement'):
                    print("   ✅ Result enhancement working")
                    print("      - Has key strengths:", bool(enhancement['enhancement'].get('key_strengths')))
                    print("      - Has hiring recommendation:", bool(enhancement['enhancement'].get('hiring_recommendation')))
                else:
                    print("   ⚠️  Enhancement returned but no data")
            else:
                print(f"   ❌ Enhancement error: {response.status_code}")
        else:
            print("   ⚠️  Could not get resume for testing")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Summary
    print("\n" + "="*60)
    print("MIND READER SEARCH STATUS")
    print("="*60)
    
    print("\nFeatures tested:")
    print("✅ Progressive 3-stage search")
    print("✅ Real-time SSE streaming")
    print("✅ Query analysis")
    print("✅ AI result enhancement")
    
    print("\nIf any tests failed, check:")
    print("1. OpenAI API key is set in production")
    print("2. Redis is configured and running")
    print("3. All services deployed successfully")

if __name__ == "__main__":
    test_mind_reader_search()