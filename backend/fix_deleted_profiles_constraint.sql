-- Fix unique constraint to exclude deleted profiles

-- 1. Drop the existing constraint
ALTER TABLE resumes DROP CONSTRAINT IF EXISTS resumes_user_id_linkedin_url_key;

-- 2. Create a partial unique index that excludes deleted profiles
-- This allows the same user to re-import a profile after deleting it
CREATE UNIQUE INDEX resumes_user_id_linkedin_url_active_key 
ON resumes (user_id, linkedin_url) 
WHERE status != 'deleted';

-- 3. Verify the change
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'resumes'
AND indexname LIKE '%linkedin%';

-- 4. Test - This should now work
-- You can have the same profile multiple times if one is deleted
/*
Example that should work after this change:
- Profile 1: user_id=X, linkedin_url=Y, status='deleted'
- Profile 2: user_id=X, linkedin_url=Y, status='active'
*/