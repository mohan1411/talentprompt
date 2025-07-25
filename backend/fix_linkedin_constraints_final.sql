-- Final fix for LinkedIn URL constraints to allow multiple users to import the same profile

-- 1. First, check what constraints and indexes currently exist
SELECT 'Current constraints:' as status;
SELECT c.conname, pg_get_constraintdef(c.oid) 
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
WHERE t.relname = 'resumes'
AND pg_get_constraintdef(c.oid) LIKE '%linkedin_url%';

SELECT 'Current indexes:' as status;
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'resumes' 
AND indexdef LIKE '%linkedin_url%';

-- 2. Drop ALL unique constraints and indexes on linkedin_url alone
-- This includes any that might have been created by migrations or manually
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Drop all UNIQUE indexes on linkedin_url column alone
    FOR r IN 
        SELECT i.relname AS index_name
        FROM pg_class t
        JOIN pg_index ix ON t.oid = ix.indrelid
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
        WHERE t.relname = 'resumes'
        AND a.attname = 'linkedin_url'
        AND ix.indisunique = true
        AND array_length(ix.indkey, 1) = 1  -- Only single-column unique indexes
    LOOP
        EXECUTE 'DROP INDEX IF EXISTS ' || quote_ident(r.index_name);
        RAISE NOTICE 'Dropped unique index: %', r.index_name;
    END LOOP;
    
    -- Drop the old constraint if it exists
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'resumes_linkedin_url_key') THEN
        ALTER TABLE resumes DROP CONSTRAINT resumes_linkedin_url_key;
        RAISE NOTICE 'Dropped constraint: resumes_linkedin_url_key';
    END IF;
END $$;

-- 3. Ensure the correct composite constraint exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'resumes_user_id_linkedin_url_key'
    ) THEN
        ALTER TABLE resumes ADD CONSTRAINT resumes_user_id_linkedin_url_key 
        UNIQUE (user_id, linkedin_url);
        RAISE NOTICE 'Created constraint: resumes_user_id_linkedin_url_key';
    ELSE
        RAISE NOTICE 'Constraint resumes_user_id_linkedin_url_key already exists';
    END IF;
END $$;

-- 4. Create a non-unique index for performance (if not exists)
CREATE INDEX IF NOT EXISTS idx_resumes_linkedin_url ON resumes(linkedin_url);

-- 5. Final verification
SELECT 'Final constraints:' as status;
SELECT c.conname, pg_get_constraintdef(c.oid) 
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
WHERE t.relname = 'resumes'
AND pg_get_constraintdef(c.oid) LIKE '%linkedin_url%';

SELECT 'Final indexes:' as status;
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'resumes' 
AND indexdef LIKE '%linkedin_url%';

-- 6. Test query - show how many users have imported each profile
SELECT 
    linkedin_url,
    COUNT(DISTINCT user_id) as user_count,
    array_agg(DISTINCT u.email) as user_emails
FROM resumes r
JOIN users u ON r.user_id = u.id
WHERE linkedin_url IN (
    'https://www.linkedin.com/in/yeshaswini-k-p-0252b2131',
    'https://www.linkedin.com/in/atul-singh-1a7421104'
)
GROUP BY linkedin_url;