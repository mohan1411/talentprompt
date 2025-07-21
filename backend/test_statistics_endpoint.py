#!/usr/bin/env python3
"""Test script for the resume statistics endpoint."""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Test credentials (update these with valid credentials)
USERNAME = "test@example.com"
PASSWORD = "testpassword"


def get_auth_token():
    """Get authentication token."""
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/login",
        data={
            "username": USERNAME,
            "password": PASSWORD
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Authentication failed: {response.status_code}")
        print(response.json())
        return None


def test_statistics_endpoint(token):
    """Test the resume statistics endpoint."""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Test different aggregation types
    aggregations = ["daily", "weekly", "monthly", "yearly"]
    
    for agg in aggregations:
        print(f"\nTesting {agg} aggregation:")
        
        # Calculate date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        params = {
            "aggregation": agg,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/resumes/statistics",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Success! Found {len(data['data'])} data points")
            print(f"  Total count: {data['total_count']}")
            print(f"  Date range: {data['start_date']} to {data['end_date']}")
            
            # Show first few data points
            if data['data']:
                print("  Sample data:")
                for item in data['data'][:3]:
                    print(f"    {item['date']}: {item['count']} resumes")
        else:
            print(f"  Failed: {response.status_code}")
            print(f"  Error: {response.json()}")


def main():
    """Main test function."""
    print("Testing Resume Statistics Endpoint")
    print("=" * 50)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("Failed to authenticate. Exiting.")
        return
    
    print("Authentication successful!")
    
    # Test the statistics endpoint
    test_statistics_endpoint(token)


if __name__ == "__main__":
    main()