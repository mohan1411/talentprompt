-- Find and fix ALL constraints preventing multiple users from importing same profile

-- 1. Show ALL constraints on the resumes table
\echo 'ALL CONSTRAINTS ON RESUMES TABLE:'
SELECT 
    c.conname AS constraint_name,
    c.contype AS type,
    pg_get_constraintdef(c.oid) AS definition
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
WHERE t.relname = 'resumes'
ORDER BY c.conname;

-- 2. Show ALL indexes on linkedin_url column
\echo '\nALL INDEXES ON LINKEDIN_URL:'
SELECT 
    i.relname AS index_name,
    ix.indisunique AS is_unique,
    pg_get_indexdef(ix.indexrelid) AS definition
FROM pg_class t
JOIN pg_index ix ON t.oid = ix.indrelid
JOIN pg_class i ON i.oid = ix.indexrelid
WHERE t.relname = 'resumes'
AND EXISTS (
    SELECT 1 FROM pg_attribute a 
    WHERE a.attrelid = t.oid 
    AND a.attnum = ANY(ix.indkey)
    AND a.attname = 'linkedin_url'
);

-- 3. Find the EXACT constraint/index causing the problem
\echo '\nCHECKING FOR PROBLEMATIC CONSTRAINTS:'
SELECT 
    'UNIQUE INDEX' as type,
    i.relname as name,
    pg_get_indexdef(ix.indexrelid) as definition
FROM pg_class t
JOIN pg_index ix ON t.oid = ix.indrelid
JOIN pg_class i ON i.oid = ix.indexrelid
JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
WHERE t.relname = 'resumes'
AND a.attname = 'linkedin_url'
AND ix.indisunique = true
AND NOT EXISTS (
    -- Exclude composite indexes with user_id
    SELECT 1 FROM pg_attribute a2
    WHERE a2.attrelid = t.oid
    AND a2.attnum = ANY(ix.indkey)
    AND a2.attname = 'user_id'
);

-- 4. Generate DROP commands for problematic constraints/indexes
\echo '\nGENERATING FIX COMMANDS:'
SELECT 
    'DROP INDEX IF EXISTS ' || i.relname || ';' as fix_command
FROM pg_class t
JOIN pg_index ix ON t.oid = ix.indrelid
JOIN pg_class i ON i.oid = ix.indexrelid
JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
WHERE t.relname = 'resumes'
AND a.attname = 'linkedin_url'
AND ix.indisunique = true
AND NOT EXISTS (
    SELECT 1 FROM pg_attribute a2
    WHERE a2.attrelid = t.oid
    AND a2.attnum = ANY(ix.indkey)
    AND a2.attname = 'user_id'
);

-- 5. Try to import test - simulate what happens
\echo '\nTEST DUPLICATE CHECK:'
-- This simulates what the application does
SELECT 
    'Would this insert fail?' as test,
    EXISTS (
        SELECT 1 FROM resumes 
        WHERE linkedin_url = 'https://www.linkedin.com/in/yeshaswini-k-p-0252b2131'
    ) as profile_exists_globally,
    EXISTS (
        SELECT 1 FROM resumes 
        WHERE linkedin_url = 'https://www.linkedin.com/in/yeshaswini-k-p-0252b2131'
        AND user_id = 'd48c0d47-d6d3-404b-9f58-8552534f9b4d'  -- your user_id
    ) as profile_exists_for_you;

-- 6. Nuclear option - drop ALL unique constraints/indexes on linkedin_url
-- ONLY RUN THIS IF ABOVE SHOWS PROBLEMATIC CONSTRAINTS
/*
-- UNCOMMENT AND RUN ONLY IF NEEDED:
DO $$
DECLARE
    cmd text;
BEGIN
    FOR cmd IN 
        SELECT 'DROP INDEX ' || i.relname
        FROM pg_class t
        JOIN pg_index ix ON t.oid = ix.indrelid
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
        WHERE t.relname = 'resumes'
        AND a.attname = 'linkedin_url'
        AND ix.indisunique = true
        AND i.relname != 'resumes_user_id_linkedin_url_key'  -- Keep the good one
    LOOP
        EXECUTE cmd;
        RAISE NOTICE 'Executed: %', cmd;
    END LOOP;
END $$;

-- Recreate the correct constraint
ALTER TABLE resumes DROP CONSTRAINT IF EXISTS resumes_user_id_linkedin_url_key;
ALTER TABLE resumes ADD CONSTRAINT resumes_user_id_linkedin_url_key UNIQUE (user_id, linkedin_url);

-- Create non-unique index for performance
CREATE INDEX IF NOT EXISTS idx_resumes_linkedin_url ON resumes(linkedin_url);
*/