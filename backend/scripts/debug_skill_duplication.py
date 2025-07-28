#!/usr/bin/env python3
"""Debug skill duplication in query analysis."""

import asyncio
from app.services.query_parser import query_parser
from app.services.gpt4_query_analyzer import gpt4_analyzer

async def debug_analysis():
    queries = ["Python", "python", "Python developer", "python developer"]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print('='*60)
        
        # Step 1: Basic parse
        basic = query_parser.parse_query(query)
        print(f"\n1. Basic parse skills: {basic['skills']}")
        
        # Step 2: Enhance basic parse (no GPT)
        enhanced = gpt4_analyzer._enhance_basic_parse(basic)
        print(f"\n2. Enhanced parse:")
        print(f"   - primary_skills: {enhanced['primary_skills']}")
        print(f"   - secondary_skills: {enhanced['secondary_skills']}")
        
        # Step 3: Full analysis (with or without GPT)
        full_analysis = await gpt4_analyzer.analyze_query(query)
        print(f"\n3. Full analysis:")
        print(f"   - primary_skills: {full_analysis.get('primary_skills', [])}")
        print(f"   - secondary_skills: {full_analysis.get('secondary_skills', [])}")
        
        # Check for duplicates
        all_skills = full_analysis.get('primary_skills', []) + full_analysis.get('secondary_skills', [])
        seen = set()
        duplicates = []
        for skill in all_skills:
            skill_lower = skill.lower()
            if skill_lower in seen:
                duplicates.append(skill)
            seen.add(skill_lower)
        
        if duplicates:
            print(f"\n⚠️  DUPLICATES FOUND: {duplicates}")

if __name__ == "__main__":
    asyncio.run(debug_analysis())