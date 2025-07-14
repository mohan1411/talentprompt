#!/usr/bin/env python3
"""Script to clear all interview-related data from the database."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import async_session_maker


async def clear_interview_data():
    """Clear all interview-related data from the database."""
    
    async with async_session_maker() as db:
        try:
            print("🗑️  Clearing interview data...")
            
            # Delete in order to respect foreign key constraints
            tables_to_clear = [
                ("interview_feedback", "interview feedback records"),
                ("interview_questions", "interview questions"),
                ("interview_sessions", "interview sessions"),
                ("candidate_journeys", "candidate journeys"),
                ("interview_templates", "interview templates"),
            ]
            
            for table_name, description in tables_to_clear:
                result = await db.execute(text(f"DELETE FROM {table_name}"))
                count = result.rowcount
                print(f"✅ Deleted {count} {description}")
            
            # Commit the transaction
            await db.commit()
            
            print("\n🎉 All interview data has been cleared successfully!")
            print("You can now start fresh with new interviews.")
            
        except Exception as e:
            print(f"\n❌ Error clearing data: {e}")
            await db.rollback()
            raise


async def main():
    """Main function."""
    print("=" * 50)
    print("INTERVIEW DATA CLEANUP TOOL")
    print("=" * 50)
    print("\nThis will delete ALL interview-related data including:")
    print("- Interview sessions")
    print("- Interview questions and responses")
    print("- Interview feedback")
    print("- Candidate journeys")
    print("- Interview templates")
    print("\n⚠️  This action cannot be undone!")
    
    response = input("\nAre you sure you want to continue? (yes/no): ")
    
    if response.lower() == 'yes':
        await clear_interview_data()
    else:
        print("\n❌ Operation cancelled.")


if __name__ == "__main__":
    asyncio.run(main())