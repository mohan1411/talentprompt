-- Diagnose Resume Indexing Issues (Fixed Version)
-- These queries work with your actual database schema

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
    LENGTH(r.embedding::text) as embedding_length,
    u.email as user_email,
    u.is_active as user_is_active
FROM resumes r
LEFT JOIN users u ON r.user_id = u.id
WHERE r.id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';

-- 2. Check if this user has other resumes with similar issues
-- Replace 'USER-ID-FROM-ABOVE' with the actual user_id from query 1
SELECT 
    id,
    first_name || ' ' || last_name as name,
    status,
    parse_status,
    embedding IS NOT NULL as has_embedding,
    created_at
FROM resumes
WHERE user_id = (
    SELECT user_id 
    FROM resumes 
    WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2'
)
ORDER BY created_at DESC;

-- 3. Find all resumes that might be causing indexing loops
-- These are active, parsed resumes without embeddings
SELECT 
    r.id,
    r.user_id,
    r.first_name || ' ' || r.last_name as name,
    r.status,
    r.parse_status,
    r.embedding IS NOT NULL as has_embedding,
    r.created_at,
    r.updated_at
FROM resumes r
WHERE 
    r.status = 'active' 
    AND r.parse_status = 'completed'
    AND (r.embedding IS NULL OR r.embedding = '[]'::jsonb)
ORDER BY r.updated_at DESC
LIMIT 20;

-- 4. Check for recently updated resumes (might be in a processing loop)
SELECT 
    id,
    first_name || ' ' || last_name as name,
    status,
    parse_status,
    updated_at,
    created_at,
    embedding IS NOT NULL as has_embedding,
    EXTRACT(EPOCH FROM (NOW() - updated_at)) as seconds_since_update
FROM resumes
WHERE updated_at > NOW() - INTERVAL '1 hour'
ORDER BY updated_at DESC
LIMIT 20;

-- 5. Database statistics
SELECT 
    'Total Resumes' as metric,
    COUNT(*) as count
FROM resumes
UNION ALL
SELECT 
    'Active Resumes' as metric,
    COUNT(*) as count
FROM resumes
WHERE status = 'active'
UNION ALL
SELECT 
    'Parsed Resumes' as metric,
    COUNT(*) as count
FROM resumes
WHERE parse_status = 'completed'
UNION ALL
SELECT 
    'Resumes with Embeddings' as metric,
    COUNT(*) as count
FROM resumes
WHERE embedding IS NOT NULL AND embedding != '[]'::jsonb
UNION ALL
SELECT 
    'Resumes without Embeddings' as metric,
    COUNT(*) as count
FROM resumes
WHERE (embedding IS NULL OR embedding = '[]'::jsonb) AND status = 'active';

-- 6. IMMEDIATE FIX - Stop the indexing loop for the problematic resume
-- This sets a valid empty embedding to prevent re-indexing attempts
UPDATE resumes
SET 
    embedding = '[]'::jsonb,
    parse_status = 'completed',
    parsed_at = COALESCE(parsed_at, NOW()),
    updated_at = NOW()
WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2'
RETURNING id, first_name, last_name, embedding IS NOT NULL as has_embedding;

-- 7. Fix all resumes that might be in indexing loops
-- This will stop all re-indexing attempts
UPDATE resumes
SET 
    embedding = COALESCE(embedding, '[]'::jsonb),
    parse_status = 'completed',
    parsed_at = COALESCE(parsed_at, NOW()),
    updated_at = NOW()
WHERE 
    status = 'active' 
    AND parse_status = 'completed'
    AND (embedding IS NULL OR embedding = '[]'::jsonb)
RETURNING id, first_name || ' ' || last_name as name;

-- 8. Alternative nuclear option - disable the problematic resume
-- Only use if the above doesn't work
-- UPDATE resumes
-- SET 
--     status = 'archived',
--     updated_at = NOW()
-- WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';

-- 9. Check for any triggers that might be causing issues
SELECT 
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE event_object_table = 'resumes';

-- 10. Check resume table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'resumes'
AND column_name IN ('id', 'user_id', 'embedding', 'parse_status', 'status')
ORDER BY ordinal_position;