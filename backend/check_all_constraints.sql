-- Comprehensive check for ALL constraints and indexes on linkedin_url column

-- 1. Check ALL constraints on the resumes table
SELECT 
    c.conname AS constraint_name,
    c.contype AS constraint_type,
    CASE c.contype
        WHEN 'c' THEN 'CHECK'
        WHEN 'f' THEN 'FOREIGN KEY'
        WHEN 'p' THEN 'PRIMARY KEY'
        WHEN 'u' THEN 'UNIQUE'
        WHEN 'x' THEN 'EXCLUDE'
    END AS constraint_type_name,
    pg_get_constraintdef(c.oid) AS definition
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
WHERE t.relname = 'resumes'
ORDER BY c.conname;

-- 2. Check ALL indexes on the resumes table
SELECT 
    i.relname AS index_name,
    a.attname AS column_name,
    ix.indisunique AS is_unique,
    ix.indisprimary AS is_primary
FROM pg_class t
JOIN pg_index ix ON t.oid = ix.indrelid
JOIN pg_class i ON i.oid = ix.indexrelid
JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
WHERE t.relname = 'resumes'
AND a.attname = 'linkedin_url'
ORDER BY i.relname;

-- 3. Check if there are any UNIQUE indexes that might act as constraints
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'resumes'
AND indexdef LIKE '%linkedin_url%'
AND indexdef LIKE '%UNIQUE%';

-- 4. Drop any unwanted constraints or indexes (CAREFUL - only run these if needed)
-- DO NOT RUN THESE AUTOMATICALLY - REVIEW RESULTS FIRST!
-- Examples:
-- DROP INDEX IF EXISTS some_unwanted_unique_index;
-- ALTER TABLE resumes DROP CONSTRAINT IF EXISTS some_unwanted_constraint;

-- 5. Final verification - show what we want to keep
SELECT 
    'EXPECTED CONSTRAINTS:' as status,
    'resumes_user_id_linkedin_url_key should exist as UNIQUE (user_id, linkedin_url)' as expected
UNION ALL
SELECT 
    'EXPECTED INDEXES:' as status,
    'idx_resumes_linkedin_url should exist as non-unique index on linkedin_url' as expected;