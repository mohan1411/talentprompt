#!/usr/bin/env python3
"""
Test script to verify Career DNA integration in progressive search.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "admin@promtitude.com"
TEST_USER_PASSWORD = "Admin123!@#"

async def get_auth_token():
    """Get authentication token."""
    async with aiohttp.ClientSession() as session:
        login_data = {
            "username": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        async with session.post(f"{API_BASE_URL}/auth/login", data=login_data) as response:
            if response.status == 200:
                data = await response.json()
                return data["access_token"]
            else:
                logger.error(f"Login failed: {await response.text()}")
                return None

async def test_progressive_search(token: str, query: str):
    """Test progressive search with SSE."""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Construct URL with query parameter
    url = f"{API_BASE_URL}/search/progressive?query={query}&limit=5&token={token}"
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing progressive search for: '{query}'")
    logger.info(f"{'='*60}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                logger.error(f"Request failed: {await response.text()}")
                return
            
            # Read SSE stream
            async for line in response.content:
                line_text = line.decode('utf-8').strip()
                
                if line_text.startswith('data: '):
                    try:
                        data = json.loads(line_text[6:])
                        
                        if data.get('event') == 'complete':
                            logger.info("Search completed")
                            break
                        elif data.get('event') == 'error':
                            logger.error(f"Search error: {data.get('message')}")
                            break
                        else:
                            # Process stage results
                            stage = data.get('stage', 'unknown')
                            stage_number = data.get('stage_number', 0)
                            result_count = data.get('count', 0)
                            timing_ms = data.get('timing_ms', 0)
                            
                            logger.info(f"\n--- Stage {stage_number}: {stage.upper()} ---")
                            logger.info(f"Results: {result_count}, Time: {timing_ms}ms")
                            
                            # Check for career DNA in enhanced stage
                            if stage == 'enhanced' and data.get('results'):
                                logger.info("\nChecking for career analytics data:")
                                
                                for i, result in enumerate(data['results'][:3]):  # Check top 3
                                    name = f"{result.get('first_name', '')} {result.get('last_name', '')}"
                                    logger.info(f"\n{i+1}. {name}")
                                    
                                    # Check for career analytics fields
                                    if 'availability_score' in result:
                                        logger.info(f"   ✓ Availability Score: {result['availability_score']:.2f}")
                                    else:
                                        logger.warning("   ✗ Availability Score: MISSING")
                                    
                                    if 'learning_velocity' in result:
                                        logger.info(f"   ✓ Learning Velocity: {result['learning_velocity']:.2f}")
                                    else:
                                        logger.warning("   ✗ Learning Velocity: MISSING")
                                    
                                    if 'career_trajectory' in result:
                                        trajectory = result['career_trajectory']
                                        logger.info(f"   ✓ Career Trajectory: {trajectory.get('pattern', 'unknown')}")
                                        logger.info(f"     - Current Level: {trajectory.get('current_level', 'unknown')}")
                                    else:
                                        logger.warning("   ✗ Career Trajectory: MISSING")
                                    
                                    if 'career_dna' in result:
                                        dna = result['career_dna']
                                        logger.info(f"   ✓ Career DNA: {dna.get('pattern', 'unknown')}")
                                        logger.info(f"     - Progression Speed: {dna.get('progression_speed', 0):.2f}")
                                        logger.info(f"     - Skill Evolution: {dna.get('skill_evolution', 'unknown')}")
                                        if dna.get('strengths'):
                                            logger.info(f"     - Strengths: {', '.join(dna['strengths'])}")
                                        if dna.get('unique_traits'):
                                            logger.info(f"     - Unique Traits: {', '.join(dna['unique_traits'])}")
                                    else:
                                        logger.warning("   ✗ Career DNA: MISSING")
                    
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON: {e}")
                        logger.error(f"Line: {line_text}")

async def main():
    """Run the test."""
    # Get auth token
    token = await get_auth_token()
    if not token:
        logger.error("Failed to authenticate")
        return
    
    logger.info("Authentication successful")
    
    # Test queries
    test_queries = [
        "Senior Python Developer with AWS",
        "Machine Learning Engineer",
        "Full Stack Developer React Node.js"
    ]
    
    for query in test_queries:
        await test_progressive_search(token, query)
        await asyncio.sleep(2)  # Small delay between tests
    
    logger.info("\n" + "="*60)
    logger.info("Test completed")
    logger.info("="*60)

if __name__ == "__main__":
    asyncio.run(main())