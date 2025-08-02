-- Stop the Resume Indexing Process
-- There's clearly a background process trying to index resumes

-- 1. Check this new problematic resume
SELECT 
    r.id,
    r.user_id,
    r.first_name,
    r.last_name,
    r.status,
    r.parse_status,
    r.embedding IS NOT NULL as has_embedding,
    r.created_at,
    r.updated_at,
    u.email as user_email
FROM resumes r
LEFT JOIN users u ON r.user_id = u.id
WHERE r.id = '7e6200c5-4209-44bf-9ba0-1caa030fd4da';

-- 2. Find ALL resumes that are being processed
-- These are likely in a queue somewhere
SELECT 
    id,
    user_id,
    first_name || ' ' || last_name as name,
    status,
    parse_status,
    embedding IS NOT NULL as has_embedding,
    created_at,
    updated_at
FROM resumes
WHERE 
    (parse_status = 'pending' OR parse_status = 'processing')
    OR (status = 'active' AND embedding IS NULL)
    OR updated_at > NOW() - INTERVAL '10 minutes'
ORDER BY updated_at DESC
LIMIT 50;

-- 3. IMMEDIATE FIX - Stop ALL indexing by marking everything as completed
-- This should stop the background process
UPDATE resumes
SET 
    parse_status = 'completed',
    embedding = CASE 
        WHEN embedding IS NULL THEN '[]'
        ELSE embedding 
    END,
    updated_at = NOW()
WHERE 
    parse_status IN ('pending', 'processing')
    OR (status = 'active' AND embedding IS NULL);

-- 4. Alternative: Mark all problematic resumes as failed
UPDATE resumes
SET 
    parse_status = 'failed',
    updated_at = NOW()
WHERE 
    (parse_status = 'pending' OR parse_status = 'processing')
    OR (status = 'active' AND embedding IS NULL AND parse_status = 'completed');

-- 5. Check for any background job tables
-- Look for tables that might contain job queues
SELECT 
    table_name
FROM information_schema.tables
WHERE 
    table_schema = 'public'
    AND (
        table_name LIKE '%job%'
        OR table_name LIKE '%queue%'
        OR table_name LIKE '%task%'
        OR table_name LIKE '%celery%'
        OR table_name LIKE '%import%'
    )
ORDER BY table_name;

-- 6. Check submission_queue if it exists
-- This might be where the indexing jobs are coming from
SELECT 
    id,
    status,
    created_at,
    processed_at,
    candidate_email
FROM submission_queue
WHERE 
    status IN ('pending', 'processing')
    OR processed_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC
LIMIT 20;

-- 7. Clear any pending submissions
UPDATE submission_queue
SET 
    status = 'completed',
    processed_at = NOW()
WHERE status IN ('pending', 'processing');

-- 8. Find the pattern - which resumes are affected?
SELECT 
    user_id,
    COUNT(*) as resume_count,
    COUNT(CASE WHEN embedding IS NULL THEN 1 END) as without_embedding,
    COUNT(CASE WHEN parse_status = 'pending' THEN 1 END) as pending_parse,
    MIN(created_at) as first_resume,
    MAX(created_at) as last_resume
FROM resumes
GROUP BY user_id
HAVING COUNT(CASE WHEN embedding IS NULL THEN 1 END) > 0
ORDER BY without_embedding DESC;

-- 9. NUCLEAR OPTION - Set ALL resumes to completed with empty embeddings
-- This will definitely stop all indexing attempts
-- UPDATE resumes
-- SET 
--     parse_status = 'completed',
--     embedding = '[]',
--     updated_at = NOW()
-- WHERE embedding IS NULL;

-- 10. Check for database connections that might be running the indexing
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    state_change,
    LEFT(query, 100) as query_preview
FROM pg_stat_activity
WHERE 
    state != 'idle'
    AND query NOT LIKE '%pg_stat_activity%'
    AND (
        query LIKE '%resume%'
        OR query LIKE '%embedding%'
        OR query LIKE '%index%'
        OR query LIKE '%vector%'
    )
ORDER BY query_start DESC;