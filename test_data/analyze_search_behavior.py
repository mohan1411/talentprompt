#!/usr/bin/env python3
"""Analyze search behavior by testing embeddings directly."""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database configuration
DB_URL = os.getenv("DATABASE_URL", "postgresql://talentprompt:talentprompt@localhost:5433/talentprompt")
# Convert to async URL if needed
if DB_URL.startswith("postgresql://"):
    ASYNC_DB_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DB_URL = DB_URL


async def analyze_search():
    """Analyze search behavior."""
    
    # Create async engine
    engine = create_async_engine(ASYNC_DB_URL, echo=False)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        print("\n=== ANALYZING SEARCH BEHAVIOR ===\n")
        
        # 1. Get a Product Manager embedding as reference
        print("1. Getting a Product Manager embedding as reference...")
        result = await session.execute(
            text("""
                SELECT id, first_name, last_name, current_title, summary, skills
                FROM resumes
                WHERE current_title = 'Product Manager'
                LIMIT 1
            """)
        )
        pm = result.fetchone()
        
        if pm:
            print(f"   Found: {pm.first_name} {pm.last_name} - {pm.current_title}")
            print(f"   Skills: {pm.skills}")
            print(f"   Summary preview: {pm.summary[:100]}...")
        
        # 2. Simulate what would happen with "product manager" search
        print("\n2. Simulating vector search for 'product manager' query...")
        print("   (Using the Product Manager's own embedding as query embedding)")
        
        result = await session.execute(
            text("""
                WITH pm_embedding AS (
                    SELECT embedding 
                    FROM resumes 
                    WHERE current_title = 'Product Manager' 
                    LIMIT 1
                )
                SELECT 
                    r.id,
                    r.first_name,
                    r.last_name,
                    r.current_title,
                    r.skills,
                    r.summary,
                    1 - (r.embedding <=> (SELECT embedding FROM pm_embedding)) as similarity
                FROM resumes r, pm_embedding
                WHERE r.embedding IS NOT NULL
                ORDER BY similarity DESC
                LIMIT 15
            """)
        )
        
        results = result.fetchall()
        
        print("\n   Top 15 results by similarity:")
        print("   " + "-" * 80)
        
        for i, row in enumerate(results, 1):
            print(f"\n   {i}. {row.first_name} {row.last_name}")
            print(f"      Title: {row.current_title}")
            print(f"      Similarity: {row.similarity:.4f}")
            print(f"      Skills: {', '.join(row.skills[:5]) if row.skills else 'None'}")
            
            # Check if "product" or "manager" appears in their content
            summary_lower = (row.summary or '').lower()
            has_product = 'product' in summary_lower
            has_manager = 'manager' in summary_lower
            
            if has_product or has_manager:
                print(f"      Keywords found: {'product' if has_product else ''} {'manager' if has_manager else ''}")
        
        # 3. Check what's in the embeddings by comparing different roles
        print("\n\n3. Comparing embeddings between different roles...")
        
        result = await session.execute(
            text("""
                WITH role_pairs AS (
                    SELECT 
                        r1.current_title as title1,
                        r2.current_title as title2,
                        1 - (r1.embedding <=> r2.embedding) as similarity
                    FROM resumes r1
                    CROSS JOIN resumes r2
                    WHERE r1.id < r2.id
                    AND r1.embedding IS NOT NULL
                    AND r2.embedding IS NOT NULL
                    AND (
                        (r1.current_title ILIKE '%product manager%' AND r2.current_title ILIKE '%developer%')
                        OR (r1.current_title ILIKE '%product manager%' AND r2.current_title ILIKE '%product%')
                        OR (r1.current_title = r2.current_title)
                    )
                )
                SELECT 
                    title1,
                    title2,
                    AVG(similarity) as avg_similarity,
                    COUNT(*) as pair_count
                FROM role_pairs
                GROUP BY title1, title2
                ORDER BY avg_similarity DESC
                LIMIT 20
            """)
        )
        
        pairs = result.fetchall()
        
        print("\n   Role pair similarities:")
        print("   " + "-" * 80)
        for title1, title2, avg_sim, count in pairs:
            print(f"   {title1:<30} <-> {title2:<30} : {avg_sim:.4f} ({count} pairs)")
        
        # 4. Let's check the actual content that gets embedded
        print("\n\n4. Checking what content is used for embeddings...")
        print("   (This would show what text is converted to embeddings)")
        
        # Get a few sample resumes with different roles
        result = await session.execute(
            text("""
                SELECT 
                    current_title,
                    first_name || ' ' || last_name as name,
                    'Title: ' || COALESCE(current_title, '') || 
                    ' Location: ' || COALESCE(location, '') ||
                    ' Experience: ' || COALESCE(years_experience::text, '') || ' years' ||
                    ' Summary: ' || COALESCE(summary, '') ||
                    ' Skills: ' || COALESCE(array_to_string(skills::text[], ', '), '') as embedding_text
                FROM resumes
                WHERE current_title IN ('Product Manager', 'Senior Software Engineer', 'Python Developer')
                LIMIT 6
            """)
        )
        
        samples = result.fetchall()
        
        print("\n   Sample embedding texts:")
        for sample in samples:
            print(f"\n   {sample.current_title} ({sample.name}):")
            print(f"   {sample.embedding_text[:200]}...")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(analyze_search())