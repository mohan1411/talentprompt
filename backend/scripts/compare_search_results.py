#!/usr/bin/env python3
"""
Compare search results between local and production environments.
This helps verify that search results are consistent.
"""

import requests
import json
from typing import List, Dict, Tuple

class SearchComparator:
    def __init__(self, local_token: str, prod_token: str):
        self.local_token = local_token
        self.prod_token = prod_token
        self.local_base = "http://localhost:8001"
        self.prod_base = "https://api.hireova.com"  # Update with your production URL
        
    def get_headers(self, is_prod: bool) -> Dict[str, str]:
        token = self.prod_token if is_prod else self.local_token
        return {"Authorization": f"Bearer {token}"}
    
    def search_progressive(self, query: str, is_prod: bool) -> List[Dict]:
        """Perform progressive search and return final results."""
        base_url = self.prod_base if is_prod else self.local_base
        url = f"{base_url}/api/v1/search/progressive?query={query}&limit=10"
        
        try:
            response = requests.get(
                url,
                headers=self.get_headers(is_prod),
                stream=True,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ {'PROD' if is_prod else 'LOCAL'} search failed: {response.status_code}")
                return []
            
            # Get the final results from the stream
            final_results = []
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8').replace('data: ', ''))
                        if data.get('stage') == 'complete':
                            final_results = data.get('results', [])
                    except:
                        pass
            
            return final_results
            
        except Exception as e:
            print(f"❌ {'PROD' if is_prod else 'LOCAL'} search error: {str(e)}")
            return []
    
    def compare_results(self, local_results: List[Dict], prod_results: List[Dict]) -> Dict:
        """Compare search results between environments."""
        comparison = {
            'local_count': len(local_results),
            'prod_count': len(prod_results),
            'count_match': len(local_results) == len(prod_results),
            'top_5_match': True,
            'score_variance': [],
            'missing_in_prod': [],
            'missing_in_local': [],
            'order_differences': []
        }
        
        # Compare top 5 results
        for i in range(min(5, len(local_results), len(prod_results))):
            local_name = f"{local_results[i]['first_name']} {local_results[i]['last_name']}"
            prod_name = f"{prod_results[i]['first_name']} {prod_results[i]['last_name']}"
            
            if local_name != prod_name:
                comparison['top_5_match'] = False
                comparison['order_differences'].append({
                    'position': i + 1,
                    'local': local_name,
                    'prod': prod_name
                })
            
            # Check score variance
            score_diff = abs(local_results[i]['score'] - prod_results[i]['score'])
            if score_diff > 0.05:  # More than 5% difference
                comparison['score_variance'].append({
                    'candidate': local_name,
                    'local_score': local_results[i]['score'],
                    'prod_score': prod_results[i]['score'],
                    'difference': score_diff
                })
        
        # Check for missing candidates
        local_names = {f"{r['first_name']} {r['last_name']}" for r in local_results}
        prod_names = {f"{r['first_name']} {r['last_name']}" for r in prod_results}
        
        comparison['missing_in_prod'] = list(local_names - prod_names)
        comparison['missing_in_local'] = list(prod_names - local_names)
        
        return comparison
    
    def run_comparison(self, test_queries: List[str]):
        """Run comparison for multiple queries."""
        print("="*60)
        print("SEARCH RESULTS COMPARISON")
        print("="*60)
        print(f"Local: {self.local_base}")
        print(f"Prod: {self.prod_base}")
        print("="*60)
        
        all_passed = True
        
        for query in test_queries:
            print(f"\n📍 Query: '{query}'")
            print("-" * 40)
            
            # Perform searches
            local_results = self.search_progressive(query, is_prod=False)
            prod_results = self.search_progressive(query, is_prod=True)
            
            # Compare results
            comparison = self.compare_results(local_results, prod_results)
            
            # Display results
            print(f"Results count: LOCAL={comparison['local_count']}, PROD={comparison['prod_count']}")
            
            if comparison['count_match'] and comparison['top_5_match'] and not comparison['score_variance']:
                print("✅ PERFECT MATCH - Results are identical")
            else:
                all_passed = False
                
                if not comparison['count_match']:
                    print(f"⚠️  Different result counts")
                
                if not comparison['top_5_match']:
                    print(f"⚠️  Top 5 results are in different order:")
                    for diff in comparison['order_differences']:
                        print(f"   Position {diff['position']}: LOCAL={diff['local']}, PROD={diff['prod']}")
                
                if comparison['score_variance']:
                    print(f"⚠️  Score differences detected:")
                    for var in comparison['score_variance']:
                        print(f"   {var['candidate']}: LOCAL={var['local_score']:.3f}, PROD={var['prod_score']:.3f}")
                
                if comparison['missing_in_prod']:
                    print(f"⚠️  Missing in PROD: {', '.join(comparison['missing_in_prod'])}")
                
                if comparison['missing_in_local']:
                    print(f"⚠️  Missing in LOCAL: {', '.join(comparison['missing_in_local'])}")
            
            # Show top 3 results from each
            print("\nTop 3 results:")
            print("LOCAL:")
            for i, r in enumerate(local_results[:3]):
                print(f"  {i+1}. {r['first_name']} {r['last_name']} (Score: {r['score']:.3f})")
            
            print("PROD:")
            for i, r in enumerate(prod_results[:3]):
                print(f"  {i+1}. {r['first_name']} {r['last_name']} (Score: {r['score']:.3f})")
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        if all_passed:
            print("✅ All queries returned consistent results!")
            print("   Search functionality is working identically in both environments.")
        else:
            print("⚠️  Some inconsistencies detected")
            print("\nPossible causes:")
            print("1. Different OpenAI API responses (embeddings may vary slightly)")
            print("2. Vector database not fully synced")
            print("3. Different resume data between environments")
            print("4. Configuration differences (models, weights, etc.)")
            print("\nRecommendations:")
            print("1. Ensure same resumes are imported in both environments")
            print("2. Wait for vector indexing to complete (5-10 minutes)")
            print("3. Check that same OpenAI models are used")

def main():
    print("Search Results Comparison Tool")
    print("="*60)
    
    # Get tokens
    print("\nYou'll need access tokens for both environments.")
    print("Get them by logging in as promtitude@gmail.com\n")
    
    local_token = input("Paste LOCAL environment token: ").strip()
    prod_token = input("Paste PRODUCTION environment token: ").strip()
    
    # Update this with your production API URL
    prod_url = input("Enter production API URL (e.g., https://api.hireova.com): ").strip()
    
    if not local_token or not prod_token:
        print("❌ Both tokens are required!")
        return
    
    # Create comparator
    comparator = SearchComparator(local_token, prod_token)
    if prod_url:
        comparator.prod_base = prod_url.rstrip('/')
    
    # Test queries
    test_queries = [
        "Python developer",
        "React TypeScript engineer",
        "Senior backend developer with AWS",
        "Full stack developer with 5 years experience",
        "DevOps engineer",
        "Machine learning engineer",
        "Frontend developer React"
    ]
    
    # Run comparison
    comparator.run_comparison(test_queries)

if __name__ == "__main__":
    main()