#!/usr/bin/env python3
"""Fix full-text search column references in production."""

import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def fix_fulltext_columns():
    """Check and fix full-text search configuration."""
    
    print("="*60)
    print("FIXING FULL-TEXT SEARCH CONFIGURATION")
    print("="*60)
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = input("\nEnter your DATABASE_URL: ").strip()
    
    # Convert to async URL if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            print("\n1. Checking actual columns in resumes table...")
            result = await session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'resumes' 
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print(f"\nFound {len(columns)} columns:")
            for col_name, col_type in columns:
                print(f"  - {col_name}: {col_type}")
            
            # Check if problematic columns exist
            column_names = [col[0] for col in columns]
            has_full_text = 'full_text' in column_names
            has_skills_text = 'skills_text' in column_names
            has_raw_text = 'raw_text' in column_names
            has_skills = 'skills' in column_names
            
            print(f"\nColumn status:")
            print(f"  - full_text column exists: {has_full_text}")
            print(f"  - skills_text column exists: {has_skills_text}")
            print(f"  - raw_text column exists: {has_raw_text}")
            print(f"  - skills column exists: {has_skills}")
            
            # Check existing indexes
            print("\n2. Checking existing indexes...")
            result = await session.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'resumes'
                AND (indexname LIKE '%gin%' OR indexname LIKE '%trgm%' OR indexname LIKE '%full%' OR indexname LIKE '%skill%')
            """))
            
            indexes = result.fetchall()
            print(f"\nFound {len(indexes)} relevant indexes:")
            for idx_name, idx_def in indexes:
                print(f"\n  Index: {idx_name}")
                # Check if index references non-existent columns
                if 'full_text' in idx_def and not has_full_text:
                    print(f"    ⚠️  References non-existent column 'full_text'")
                if 'skills_text' in idx_def and not has_skills_text:
                    print(f"    ⚠️  References non-existent column 'skills_text'")
            
            # Drop problematic indexes
            print("\n3. Dropping indexes that reference non-existent columns...")
            for idx_name, idx_def in indexes:
                if ('full_text' in idx_def and not has_full_text) or ('skills_text' in idx_def and not has_skills_text):
                    print(f"   Dropping {idx_name}...")
                    try:
                        await session.execute(text(f"DROP INDEX IF EXISTS {idx_name}"))
                        print(f"   ✅ Dropped {idx_name}")
                    except Exception as e:
                        print(f"   ❌ Error dropping {idx_name}: {str(e)}")
            
            # Create correct indexes
            print("\n4. Creating correct indexes...")
            
            # Ensure pg_trgm extension exists
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            print("   ✅ pg_trgm extension ready")
            
            if has_raw_text:
                print("   Creating GIN index on raw_text...")
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_resumes_raw_text_gin 
                    ON resumes USING GIN (to_tsvector('english', COALESCE(raw_text, '')))
                """))
                print("   ✅ Created raw_text GIN index")
            
            if has_skills:
                print("   Creating GIN index on skills array...")
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_resumes_skills_gin 
                    ON resumes USING GIN (to_tsvector('english', COALESCE(skills::text, '')))
                """))
                print("   ✅ Created skills GIN index")
                
                print("   Creating trigram index on skills...")
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_resumes_skills_trgm 
                    ON resumes USING GIN ((skills::text) gin_trgm_ops)
                """))
                print("   ✅ Created skills trigram index")
            
            # Create composite search index
            print("   Creating composite search index...")
            text_fields = []
            if has_raw_text:
                text_fields.append("COALESCE(raw_text, '')")
            if 'summary' in column_names:
                text_fields.append("COALESCE(summary, '')")
            if 'current_title' in column_names:
                text_fields.append("COALESCE(current_title, '')")
            if has_skills:
                text_fields.append("COALESCE(skills::text, '')")
            
            if text_fields:
                composite_expr = " || ' ' || ".join(text_fields)
                await session.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_resumes_composite_search_gin 
                    ON resumes USING GIN (to_tsvector('english', {composite_expr}))
                """))
                print("   ✅ Created composite search index")
            
            # Commit changes
            await session.commit()
            
            print("\n✅ Full-text search configuration fixed!")
            print("\nThe search should now work correctly with:")
            print("- raw_text column for resume content")
            print("- skills array column for skills")
            print("- Proper GIN and trigram indexes")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_fulltext_columns())