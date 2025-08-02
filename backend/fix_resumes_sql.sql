-- Fix Resume User ID Issue
-- Run these queries in PgAdmin to fix resumes without user_id

-- 1. First, check how many resumes have NULL user_id
SELECT COUNT(*) as orphaned_resume_count 
FROM resumes 
WHERE user_id IS NULL;

-- 2. Show details of orphaned resumes (first 10)
SELECT 
    id, 
    first_name, 
    last_name, 
    email,
    created_at,
    status,
    parse_status
FROM resumes 
WHERE user_id IS NULL
ORDER BY created_at DESC
LIMIT 10;

-- 3. Check if the specific problematic resume exists
SELECT 
    id, 
    first_name, 
    last_name, 
    user_id,
    created_at,
    status
FROM resumes 
WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';

-- 4. Find an active user to assign orphaned resumes to
-- (Usually the first/admin user or most active user)
SELECT 
    id, 
    email, 
    full_name,
    created_at,
    (SELECT COUNT(*) FROM resumes WHERE user_id = users.id) as resume_count
FROM users 
WHERE is_active = true 
ORDER BY created_at ASC
LIMIT 5;

-- 5. IMPORTANT: Update this user_id before running the UPDATE query
-- Replace 'YOUR-USER-ID-HERE' with an actual user ID from the query above
-- Example: 'a1234567-89ab-cdef-0123-456789abcdef'

-- 6. Fix all orphaned resumes by assigning them to a user
-- IMPORTANT: Replace 'YOUR-USER-ID-HERE' with the actual user ID!
UPDATE resumes 
SET 
    user_id = 'YOUR-USER-ID-HERE',  -- ⚠️ REPLACE THIS!
    updated_at = NOW()
WHERE user_id IS NULL;

-- 7. Verify the fix worked
SELECT COUNT(*) as remaining_orphaned 
FROM resumes 
WHERE user_id IS NULL;

-- 8. Check the specific problematic resume again
SELECT 
    id, 
    first_name, 
    last_name, 
    user_id,
    status
FROM resumes 
WHERE id = '4772e109-7dd4-43b4-9c31-a36c0095fea2';

-- 9. Optional: Add constraint to prevent future issues
-- This will fail if there are still NULL user_ids
ALTER TABLE resumes 
ALTER COLUMN user_id SET NOT NULL;

-- 10. Show current database statistics
SELECT 
    'Active Users' as metric,
    COUNT(*) as count
FROM users 
WHERE is_active = true
UNION ALL
SELECT 
    'Total Resumes' as metric,
    COUNT(*) as count
FROM resumes
UNION ALL
SELECT 
    'Orphaned Resumes' as metric,
    COUNT(*) as count
FROM resumes 
WHERE user_id IS NULL
UNION ALL
SELECT 
    'Parsed Resumes' as metric,
    COUNT(*) as count
FROM resumes 
WHERE parse_status = 'completed';

-- 11. If you need to find which resumes are causing indexing errors
-- Look for resumes that might be in a bad state
SELECT 
    id,
    first_name || ' ' || last_name as name,
    user_id,
    status,
    parse_status,
    created_at
FROM resumes
WHERE 
    (user_id IS NULL 
    OR status = 'active' AND parse_status = 'completed')
ORDER BY created_at DESC
LIMIT 20;