-- Verify and fix LinkedIn URL constraints

-- 1. Check current constraints
SELECT 
    c.conname AS constraint_name,
    c.contype AS constraint_type,
    pg_get_constraintdef(c.oid) AS definition
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
WHERE t.relname = 'resumes'
AND c.conname LIKE '%linkedin%'
ORDER BY c.conname;

-- 2. Check for any duplicate linkedin_urls across different users
SELECT 
    linkedin_url, 
    COUNT(DISTINCT user_id) as user_count,
    COUNT(*) as total_count,
    array_agg(DISTINCT user_id) as user_ids
FROM resumes
WHERE linkedin_url IS NOT NULL
GROUP BY linkedin_url
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC
LIMIT 10;

-- 3. Drop the old constraint if it exists
ALTER TABLE resumes DROP CONSTRAINT IF EXISTS resumes_linkedin_url_key;

-- 4. Try to add the new constraint
DO $$
BEGIN
    -- Check if constraint already exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'resumes_user_id_linkedin_url_key'
    ) THEN
        -- Add the new constraint
        ALTER TABLE resumes ADD CONSTRAINT resumes_user_id_linkedin_url_key 
        UNIQUE (user_id, linkedin_url);
        RAISE NOTICE 'Constraint resumes_user_id_linkedin_url_key created successfully';
    ELSE
        RAISE NOTICE 'Constraint resumes_user_id_linkedin_url_key already exists';
    END IF;
END $$;

-- 5. Create index if not exists
CREATE INDEX IF NOT EXISTS idx_resumes_linkedin_url ON resumes(linkedin_url);

-- 6. Verify the final state
SELECT 
    'Final constraints:' as status,
    c.conname AS constraint_name,
    c.contype AS constraint_type,
    pg_get_constraintdef(c.oid) AS definition
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
WHERE t.relname = 'resumes'
AND (c.conname LIKE '%linkedin%' OR c.conname LIKE '%user_id%')
ORDER BY c.conname;