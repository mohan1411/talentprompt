-- Diagnose Resume Indexing Issues
-- If there are no orphaned resumes, the issue might be something else

-- 1. Check the specific problematic resume
SELECT 
    r.id,
    r.user_id,
    r.first_name,
    r.last_name,
    r.status,
    r.parse_status,
    r.created_at,
    r.parsed_at,
    r.embedding IS NOT NULL as has_embedding,
    u.email as user_email,
    u.is_active as user_is_active
FROM resumes r
LEFT JOIN users u ON r.user_id = u.id
WHERE r.id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';

-- 2. Check if the user exists and is active
SELECT 
    id,
    email,
    is_active,
    created_at
FROM users
WHERE id = (
    SELECT user_id 
    FROM resumes 
    WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2'
);

-- 3. Find all resumes that might have indexing issues
-- Resumes that are active and parsed but might not be indexed properly
SELECT 
    r.id,
    r.user_id,
    r.first_name || ' ' || r.last_name as name,
    r.status,
    r.parse_status,
    r.embedding IS NOT NULL as has_embedding,
    r.created_at,
    u.is_active as user_active
FROM resumes r
LEFT JOIN users u ON r.user_id = u.id
WHERE 
    r.status = 'active' 
    AND r.parse_status = 'completed'
    AND (
        r.embedding IS NULL 
        OR u.is_active = false
        OR u.id IS NULL
    )
ORDER BY r.created_at DESC
LIMIT 20;

-- 4. Check for data type issues with user_id
-- Sometimes the issue is that user_id is stored as a string or has formatting issues
SELECT 
    id,
    user_id,
    pg_typeof(user_id) as user_id_type,
    LENGTH(user_id::text) as user_id_length,
    user_id::text as user_id_as_text
FROM resumes
WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';

-- 5. Check if there are any resumes with malformed UUIDs
SELECT 
    id,
    user_id,
    first_name,
    last_name
FROM resumes
WHERE 
    user_id IS NOT NULL
    AND NOT (user_id::text ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
LIMIT 10;

-- 6. Check import_queue for issues
-- Maybe the resume is being reimported repeatedly
SELECT 
    iq.id,
    iq.user_id,
    iq.status,
    iq.resume_id,
    iq.created_at,
    iq.error_message
FROM import_queue_items iq
WHERE 
    iq.resume_id = '4772e109-7dd4-43b4-9c31-a36c0095fea2'
    OR iq.profile_data::text LIKE '%4772e109-7dd4-43b4-9c31-a36c0095fea2%'
ORDER BY iq.created_at DESC;

-- 7. Force re-parse the problematic resume
-- This might help if the issue is with the parsing state
UPDATE resumes
SET 
    parse_status = 'pending',
    embedding = NULL,
    updated_at = NOW()
WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';

-- 8. Check for any background jobs or tasks
-- Look for any recurring processes that might be trying to reindex
SELECT 
    'Total Resumes' as metric,
    COUNT(*) as count
FROM resumes
UNION ALL
SELECT 
    'Pending Parse' as metric,
    COUNT(*) as count
FROM resumes
WHERE parse_status = 'pending'
UNION ALL
SELECT 
    'Without Embeddings' as metric,
    COUNT(*) as count
FROM resumes
WHERE embedding IS NULL AND status = 'active'
UNION ALL
SELECT 
    'Import Queue Items' as metric,
    COUNT(*) as count
FROM import_queue_items
WHERE status IN ('pending', 'processing');

-- 9. Check if the issue is with a specific user's resumes
SELECT 
    u.id as user_id,
    u.email,
    COUNT(r.id) as resume_count,
    COUNT(CASE WHEN r.embedding IS NULL THEN 1 END) as without_embedding,
    COUNT(CASE WHEN r.parse_status = 'pending' THEN 1 END) as pending_parse
FROM users u
LEFT JOIN resumes r ON u.id = r.user_id
GROUP BY u.id, u.email
HAVING COUNT(CASE WHEN r.embedding IS NULL THEN 1 END) > 0
ORDER BY without_embedding DESC
LIMIT 10;

-- 10. Emergency fix: Clear the embedding for the problematic resume
-- This will stop the indexing attempts
UPDATE resumes
SET 
    embedding = '[]'::jsonb,  -- Empty embedding
    parse_status = 'completed',
    parsed_at = NOW(),
    updated_at = NOW()
WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';

-- 11. Alternative: Mark the resume as deleted to stop processing
-- Only use if nothing else works
-- UPDATE resumes
-- SET 
--     status = 'deleted',
--     updated_at = NOW()
-- WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';