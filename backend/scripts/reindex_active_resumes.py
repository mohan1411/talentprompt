#!/usr/bin/env python3
"""
Reindex only active resumes in vector search.
Only run this if needed!
"""

import asyncio
import sys
sys.path.append('..')

from app.core.config import settings
from app.db.session import async_session
from app.services.vector_search import vector_search
from app.services.resume_processor import resume_processor
from sqlalchemy import select
from app.models.resume import Resume
from app.models.user import User

async def reindex_active_resumes():
    print("="*60)
    print("REINDEXING ACTIVE RESUMES")
    print("="*60)
    
    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set!")
        return
    
    async with async_session() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.email == "promtitude@gmail.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User not found!")
            return
        
        # Get active resumes
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user.id)
            .where(Resume.status != 'deleted')
            .order_by(Resume.created_at.desc())
        )
        resumes = result.scalars().all()
        
        print(f"\nFound {len(resumes)} active resumes to reindex")
        
        # Initialize vector search
        await vector_search.initialize()
        
        # Process each resume
        success_count = 0
        for i, resume in enumerate(resumes):
            try:
                print(f"\n[{i+1}/{len(resumes)}] Processing {resume.first_name} {resume.last_name}...")
                
                # Generate embeddings and index
                if resume.raw_text:
                    # Create search text
                    search_text = resume_processor._create_search_text(resume)
                    
                    # Generate embedding
                    embedding = await resume_processor._generate_embedding(search_text)
                    
                    if embedding:
                        # Index in vector search
                        await vector_search.index_resume(
                            resume_id=str(resume.id),
                            text=search_text,
                            metadata={
                                "user_id": str(resume.user_id),  # CRITICAL: Include user_id for security
                                "first_name": resume.first_name,
                                "last_name": resume.last_name,
                                "skills": resume.skills or [],
                                "location": resume.location,
                                "years_experience": resume.years_experience,
                                "current_title": resume.current_title
                            }
                        )
                        print(f"   ✅ Indexed successfully")
                        success_count += 1
                    else:
                        print(f"   ⚠️  Failed to generate embedding")
                else:
                    print(f"   ⚠️  No raw text available")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        
        print(f"\n✅ Reindexing complete!")
        print(f"   Successfully indexed: {success_count}/{len(resumes)} resumes")
        
        # Clean up deleted resumes from Qdrant (optional)
        print("\nCleaning up deleted resumes from vector index...")
        try:
            # Get all resume IDs from Qdrant
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Search for all vectors for this user
            search_result = await vector_search.client.search(
                collection_name="resumes",
                query_vector=[0] * 1536,  # Dummy vector
                limit=1000,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=str(user.id))
                        )
                    ]
                )
            )
            
            # Get active resume IDs
            active_ids = {str(r.id) for r in resumes}
            
            # Find vectors to delete
            vectors_to_delete = []
            for hit in search_result:
                if hit.id not in active_ids:
                    vectors_to_delete.append(hit.id)
            
            if vectors_to_delete:
                print(f"   Found {len(vectors_to_delete)} vectors for deleted resumes")
                # Delete them
                await vector_search.client.delete(
                    collection_name="resumes",
                    points_selector=vectors_to_delete
                )
                print(f"   ✅ Cleaned up {len(vectors_to_delete)} obsolete vectors")
            else:
                print("   ✅ No obsolete vectors found")
                
        except Exception as e:
            print(f"   ⚠️  Cleanup failed: {str(e)}")

if __name__ == "__main__":
    print("\n⚠️  This will reindex all active resumes.")
    print("   This process may take a few minutes and will use OpenAI API credits.")
    
    confirm = input("\nContinue? (yes/no): ").lower().strip()
    if confirm == "yes":
        asyncio.run(reindex_active_resumes())
    else:
        print("Cancelled.")