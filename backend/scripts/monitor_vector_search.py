#!/usr/bin/env python3
"""Monitor vector search status and performance."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func, cast, String

from app.core.config import settings
from app.models.user import User
from app.models.resume import Resume
from app.services.vector_search import vector_search
from app.services.search import search_service


class VectorSearchMonitor:
    """Monitor vector search system status and performance."""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
    
    async def setup(self):
        """Initialize database connection."""
        self.engine = create_async_engine(settings.DATABASE_URL)
        self.async_session = async_sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
    
    async def cleanup(self):
        """Clean up database connection."""
        if self.engine:
            await self.engine.dispose()
    
    async def display_dashboard(self):
        """Display comprehensive dashboard."""
        print("\n" + "="*80)
        print("🔍 VECTOR SEARCH MONITORING DASHBOARD")
        print("="*80)
        print(f"Generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("="*80 + "\n")
        
        async with self.async_session() as db:
            await self._display_system_status()
            await self._display_user_statistics(db)
            await self._display_index_health(db)
            await self._display_popular_skills(db)
            await self._display_search_examples(db)
            await self._display_performance_metrics(db)
    
    async def _display_system_status(self):
        """Display Qdrant system status."""
        print("📊 SYSTEM STATUS")
        print("-" * 50)
        
        try:
            info = await vector_search.get_collection_info()
            print(f"  Qdrant Status: {info.get('status', 'Unknown')}")
            print(f"  Collection: {info.get('collection', 'Unknown')}")
            print(f"  Total Vectors: {info.get('points_count', 0):,}")
            
            # Estimate memory usage (rough calculation)
            vector_count = info.get('points_count', 0)
            dims = 1536  # OpenAI ada-002 dimensions
            bytes_per_float = 4
            vector_memory_mb = (vector_count * dims * bytes_per_float) / (1024 * 1024)
            print(f"  Estimated Vector Memory: {vector_memory_mb:.1f} MB")
            
        except Exception as e:
            print(f"  ❌ Error connecting to Qdrant: {e}")
        
        print()
    
    async def _display_user_statistics(self, db: AsyncSession):
        """Display per-user statistics."""
        print("👥 USER STATISTICS")
        print("-" * 50)
        
        # Get user resume counts
        stmt = select(
            User.email,
            User.id,
            func.count(Resume.id).label('total_resumes')
        ).outerjoin(Resume).group_by(User.id, User.email)
        
        result = await db.execute(stmt)
        user_stats = result.all()
        
        print(f"  Total Users: {len(user_stats)}")
        print("\n  Per-User Resume Counts:")
        
        for email, user_id, total in user_stats:
            if total > 0:
                # Get indexed count separately
                indexed_stmt = select(func.count(Resume.id)).where(
                    Resume.user_id == user_id,
                    Resume.status == 'active',
                    Resume.parse_status == 'completed'
                )
                indexed_result = await db.execute(indexed_stmt)
                indexed = indexed_result.scalar() or 0
                
                percentage = (indexed / total * 100) if total > 0 else 0
                print(f"    • {email}")
                print(f"      Total: {total} | Indexed: {indexed} ({percentage:.1f}%)")
        
        print()
    
    async def _display_index_health(self, db: AsyncSession):
        """Check and display index health."""
        print("🏥 INDEX HEALTH CHECK")
        print("-" * 50)
        
        # Get all active resumes from PostgreSQL
        pg_stmt = select(Resume.id).where(
            Resume.status == 'active',
            Resume.parse_status == 'completed'
        )
        pg_result = await db.execute(pg_stmt)
        pg_ids = {str(row[0]) for row in pg_result.all()}
        
        print(f"  PostgreSQL active resumes: {len(pg_ids)}")
        
        # Check a sample to verify they're in Qdrant
        sample_ids = list(pg_ids)[:10]  # Check first 10
        missing_count = 0
        
        for resume_id in sample_ids:
            try:
                # Try to search for this specific resume
                results = await vector_search.search_similar(
                    query="test",
                    limit=1000
                )
                found = any(r['resume_id'] == resume_id for r in results)
                if not found:
                    missing_count += 1
            except:
                pass
        
        if missing_count > 0:
            print(f"  ⚠️  Warning: {missing_count}/{len(sample_ids)} sampled resumes missing from index")
            print("     Consider running reindex script")
        else:
            print("  ✅ Index health: Good (sample check passed)")
        
        print()
    
    async def _display_popular_skills(self, db: AsyncSession):
        """Display most popular skills across all resumes."""
        print("🔧 TOP SKILLS IN DATABASE")
        print("-" * 50)
        
        # Get all skills
        stmt = select(Resume.skills).where(
            Resume.skills.isnot(None),
            Resume.status == 'active'
        )
        result = await db.execute(stmt)
        all_skills_lists = result.scalars().all()
        
        # Count skills
        skill_counter = Counter()
        for skills_list in all_skills_lists:
            if skills_list:
                for skill in skills_list:
                    if skill:
                        skill_counter[skill] += 1
        
        # Display top 15 skills
        print("  Most Common Skills:")
        for skill, count in skill_counter.most_common(15):
            bar = "█" * int(count / max(skill_counter.values()) * 20)
            print(f"    {skill:<20} {bar} ({count})")
        
        print()
    
    async def _display_search_examples(self, db: AsyncSession):
        """Display example searches with results."""
        print("🔍 EXAMPLE SEARCHES")
        print("-" * 50)
        
        # Get a sample user for testing
        user_stmt = select(User).limit(1)
        user_result = await db.execute(user_stmt)
        sample_user = user_result.scalar_one_or_none()
        
        if not sample_user:
            print("  No users found for example searches")
            return
        
        example_queries = [
            ("Python Backend", "python backend developer"),
            ("ML Engineer", "machine learning engineer"),
            ("Senior Full Stack", "senior full stack developer"),
            ("Cloud DevOps", "aws kubernetes devops"),
            ("Data Science", "data scientist python R")
        ]
        
        print(f"  Running example searches for user: {sample_user.email}\n")
        
        for label, query in example_queries:
            results = await search_service.search_resumes(
                db, query, sample_user.id, limit=3
            )
            
            print(f"  {label}: \"{query}\"")
            if results:
                print(f"    Found {len(results)} results:")
                for i, (resume, score) in enumerate(results[:2], 1):
                    print(f"      {i}. {resume['first_name']} {resume['last_name']} - {resume.get('current_title', 'N/A')}")
                    print(f"         Score: {score:.3f} | Skills: {', '.join(resume.get('skills', [])[:3])}...")
            else:
                print("    No results found")
            print()
    
    async def _display_performance_metrics(self, db: AsyncSession):
        """Display performance metrics."""
        print("⚡ PERFORMANCE METRICS")
        print("-" * 50)
        
        # Test search performance
        test_queries = ["python", "senior developer", "machine learning engineer"]
        
        # Get a user for testing
        user_stmt = select(User).limit(1)
        user_result = await db.execute(user_stmt)
        test_user = user_result.scalar_one_or_none()
        
        if test_user:
            print("  Search Response Times:")
            
            for query in test_queries:
                import time
                start = time.time()
                results = await search_service.search_resumes(
                    db, query, test_user.id, limit=10
                )
                elapsed = time.time() - start
                
                print(f"    '{query}': {elapsed:.3f}s ({len(results)} results)")
        
        print("\n  Recommendations:")
        print("    • Keep response times under 500ms for best UX")
        print("    • Monitor Qdrant memory usage as collection grows")
        print("    • Run reindexing script after bulk imports")
        print("    • Consider adding caching for frequent queries")


async def main():
    """Run the monitoring dashboard."""
    monitor = VectorSearchMonitor()
    
    try:
        await monitor.setup()
        await monitor.display_dashboard()
    finally:
        await monitor.cleanup()


if __name__ == "__main__":
    asyncio.run(main())