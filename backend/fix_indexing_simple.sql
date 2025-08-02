-- Simple Fix for Resume Indexing Issues
-- Compatible with different PostgreSQL versions and column types

-- 1. First, check what type the embedding column is
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'resumes'
AND column_name = 'embedding';

-- 2. Check the problematic resume
SELECT 
    r.id,
    r.user_id,
    r.first_name,
    r.last_name,
    r.status,
    r.parse_status,
    r.embedding IS NOT NULL as has_embedding,
    u.email as user_email
FROM resumes r
LEFT JOIN users u ON r.user_id = u.id
WHERE r.id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';

-- 3. IMMEDIATE FIX - Option A: If embedding is JSON/JSONB type
UPDATE resumes
SET 
    embedding = '[]',
    parse_status = 'completed',
    parsed_at = NOW(),
    updated_at = NOW()
WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';

-- 4. IMMEDIATE FIX - Option B: If embedding is TEXT type
-- UPDATE resumes
-- SET 
--     embedding = '[]',
--     parse_status = 'completed',
--     parsed_at = NOW(),
--     updated_at = NOW()
-- WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';

-- 5. IMMEDIATE FIX - Option C: Set embedding to NULL
-- UPDATE resumes
-- SET 
--     embedding = NULL,
--     parse_status = 'failed',
--     parsed_at = NOW(),
--     updated_at = NOW()
-- WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';

-- 6. Check recently updated resumes (might be in a loop)
SELECT 
    id,
    first_name || ' ' || last_name as name,
    status,
    parse_status,
    updated_at,
    embedding IS NOT NULL as has_embedding
FROM resumes
WHERE updated_at > NOW() - INTERVAL '1 hour'
ORDER BY updated_at DESC
LIMIT 10;

-- 7. Nuclear option - Archive the problematic resume
-- UPDATE resumes
-- SET 
--     status = 'archived',
--     updated_at = NOW()
-- WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';

-- 8. Find all resumes that might be causing issues
SELECT 
    COUNT(*) as count,
    status,
    parse_status,
    embedding IS NOT NULL as has_embedding
FROM resumes
GROUP BY status, parse_status, embedding IS NOT NULL
ORDER BY count DESC;

-- 9. Simple fix for all problematic resumes
-- This marks them as failed to stop the indexing loop
UPDATE resumes
SET 
    parse_status = 'failed',
    updated_at = NOW()
WHERE 
    status = 'active' 
    AND parse_status = 'completed'
    AND embedding IS NULL;

-- 10. Alternative: Delete the problematic resume completely
-- Only use as last resort!
-- DELETE FROM resumes WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';