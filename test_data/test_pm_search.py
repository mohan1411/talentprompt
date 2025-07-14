#!/usr/bin/env python3
"""Script to test product manager search and see what results come back."""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import the services
from app.services.embeddings import embedding_service
from app.services.search import search_service

# Database configuration
DB_URL = os.getenv("DATABASE_URL", "postgresql://talentprompt:talentprompt@localhost:5433/talentprompt")
# Convert to async URL if needed
if DB_URL.startswith("postgresql://"):
    ASYNC_DB_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DB_URL = DB_URL


async def test_search_query(query: str):
    """Test a search query and show results."""
    
    # Create async engine
    engine = create_async_engine(ASYNC_DB_URL, echo=False)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        print(f"\n=== TESTING SEARCH FOR: '{query}' ===\n")
        
        # 1. Generate embedding for the query
        print("1. Generating embedding for query...")
        query_embedding = await embedding_service.generate_embedding(query)
        if query_embedding:
            print(f"   Embedding generated (dimension: {len(query_embedding)})")
        else:
            print("   ERROR: Failed to generate embedding!")
            return
        
        # 2. Perform the search
        print("\n2. Performing vector search...")
        results = await search_service.search_resumes(
            session,
            query=query,
            limit=10
        )
        
        print(f"\n3. Found {len(results)} results:")
        print("-" * 80)
        
        for i, (resume, score) in enumerate(results, 1):
            print(f"\n{i}. {resume['first_name']} {resume['last_name']}")
            print(f"   Current Title: {resume.get('current_title', 'N/A')}")
            print(f"   Similarity Score: {score:.4f}")
            print(f"   Years Experience: {resume.get('years_experience', 'N/A')}")
            print(f"   Location: {resume.get('location', 'N/A')}")
            
            # Show skills
            skills = resume.get('skills', [])
            if skills:
                print(f"   Skills: {', '.join(skills[:5])}" + (" ..." if len(skills) > 5 else ""))
            
            # Show summary snippet
            summary = resume.get('summary', '')
            if summary:
                print(f"   Summary: {summary[:150]}...")
        
        # 4. Let's also check what a direct SQL query would return
        print("\n\n4. Direct SQL query for titles containing 'product manager':")
        print("-" * 80)
        
        result = await session.execute(
            text("""
                SELECT 
                    id, first_name, last_name, current_title,
                    1 - (embedding <=> (SELECT embedding FROM resumes WHERE current_title ILIKE '%product manager%' LIMIT 1)) as similarity
                FROM resumes
                WHERE current_title ILIKE '%product manager%'
                ORDER BY similarity DESC
                LIMIT 5
            """)
        )
        
        pm_results = result.fetchall()
        for row in pm_results:
            print(f"   {row.first_name} {row.last_name} - {row.current_title} (similarity to first PM: {row.similarity:.4f})")
    
    await engine.dispose()


async def compare_embeddings():
    """Compare embeddings between Product Managers and Developers."""
    
    # Create async engine
    engine = create_async_engine(ASYNC_DB_URL, echo=False)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        print("\n\n=== COMPARING EMBEDDINGS ===\n")
        
        # Get a Product Manager embedding
        result = await session.execute(
            text("""
                SELECT id, first_name, last_name, current_title, embedding
                FROM resumes
                WHERE current_title ILIKE '%product manager%'
                AND embedding IS NOT NULL
                LIMIT 1
            """)
        )
        pm = result.fetchone()
        
        if not pm:
            print("No Product Manager found with embedding!")
            return
        
        print(f"Reference: {pm.first_name} {pm.last_name} - {pm.current_title}")
        
        # Compare with other roles
        result = await session.execute(
            text("""
                SELECT 
                    current_title,
                    AVG(1 - (embedding <=> :pm_embedding)) as avg_similarity,
                    COUNT(*) as count
                FROM resumes
                WHERE embedding IS NOT NULL
                GROUP BY current_title
                ORDER BY avg_similarity DESC
                LIMIT 15
            """),
            {"pm_embedding": pm.embedding}
        )
        
        similarities = result.fetchall()
        
        print("\nAverage similarity to Product Manager role by title:")
        print("-" * 60)
        for title, avg_sim, count in similarities:
            print(f"{title:<35} {avg_sim:.4f} ({count} resumes)")
    
    await engine.dispose()


async def main():
    """Main function."""
    try:
        # Test the search
        await test_search_query("product manager")
        
        # Compare embeddings
        await compare_embeddings()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())