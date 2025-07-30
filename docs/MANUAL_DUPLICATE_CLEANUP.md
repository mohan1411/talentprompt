# Manual Duplicate Resume Cleanup

If the automated scripts don't work due to environment issues, here's how to manually clean up duplicates.

## Option 1: Direct Database Query (PostgreSQL)

Connect to your database and run:

```sql
-- First, see all duplicates
WITH duplicate_resumes AS (
    SELECT 
        email,
        user_id,
        COUNT(*) as duplicate_count,
        MIN(created_at) as oldest_created,
        MAX(created_at) as newest_created
    FROM resumes
    WHERE status = 'active'
    GROUP BY email, user_id
    HAVING COUNT(*) > 1
)
SELECT * FROM duplicate_resumes;

-- Mark older duplicates as deleted (keeping the newest)
WITH newest_resumes AS (
    SELECT DISTINCT ON (email, user_id) 
        id
    FROM resumes
    WHERE status = 'active'
    ORDER BY email, user_id, created_at DESC
)
UPDATE resumes
SET status = 'deleted',
    updated_at = CURRENT_TIMESTAMP
WHERE status = 'active'
    AND id NOT IN (SELECT id FROM newest_resumes);
```

## Option 2: Using Python REPL

From the backend directory:

```python
# Start Python
python

# Import necessary modules
import asyncio
from sqlalchemy import select, and_, func
from app.db.session import async_session_maker
from app.models.resume import Resume

# Function to check duplicates
async def check_duplicates():
    async with async_session_maker() as db:
        # Find duplicates
        query = select(
            Resume.email,
            Resume.user_id,
            func.count(Resume.id)
        ).where(
            Resume.status == 'active'
        ).group_by(
            Resume.email, Resume.user_id
        ).having(
            func.count(Resume.id) > 1
        )
        
        result = await db.execute(query)
        duplicates = result.all()
        
        for email, user_id, count in duplicates:
            print(f"Email: {email}, Recruiter: {user_id}, Count: {count}")

# Run the check
asyncio.run(check_duplicates())
```

## Option 3: Through the Application

1. **Identify duplicates** in the resume list
2. **Note the older entries** (check upload dates)
3. **Delete manually** using the delete button on each duplicate

## Option 4: Create a Simple Script

Create a file `cleanup.py` in the backend directory:

```python
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variables if needed
os.environ['DATABASE_URL'] = 'your_database_url_here'

import asyncio
from sqlalchemy import select, and_
from app.db.session import async_session_maker
from app.models.resume import Resume

async def cleanup():
    async with async_session_maker() as db:
        # Get all resumes ordered by email and creation date
        result = await db.execute(
            select(Resume)
            .where(Resume.status == 'active')
            .order_by(Resume.email, Resume.created_at.desc())
        )
        resumes = result.scalars().all()
        
        seen = set()
        for resume in resumes:
            key = (resume.email, resume.user_id)
            if key in seen:
                print(f"Marking duplicate as deleted: {resume.email} - {resume.first_name} {resume.last_name}")
                resume.status = 'deleted'
            else:
                seen.add(key)
        
        await db.commit()
        print("Cleanup complete!")

asyncio.run(cleanup())
```

## Prevention Going Forward

The system now checks for existing resumes before creating new ones:
- Email is used as the unique identifier per recruiter
- New submissions update existing resumes instead of creating duplicates
- This prevents future duplicates from being created