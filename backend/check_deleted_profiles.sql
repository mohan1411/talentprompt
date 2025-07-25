-- Check if you have these profiles with deleted status

-- Check ALL your profiles (including deleted ones)
SELECT 
    r.id,
    r.first_name,
    r.last_name,
    r.linkedin_url,
    r.status,
    r.created_at,
    r.updated_at
FROM resumes r
WHERE r.user_id = 'd48c0d47-d6d3-404b-9f58-8552534f9b4d'  -- your user_id from earlier query
AND (
    r.linkedin_url LIKE '%yeshaswini-k-p-0252b2131%'
    OR r.linkedin_url LIKE '%atul-singh-1a7421104%'
    OR r.linkedin_url LIKE '%ravikant-kumar%'
)
ORDER BY r.created_at DESC;

-- Check what your duplicate check would find
SELECT 
    'Duplicate check results:' as check,
    r.linkedin_url,
    r.status,
    r.user_id = 'd48c0d47-d6d3-404b-9f58-8552534f9b4d' as is_yours
FROM resumes r
WHERE r.linkedin_url IN (
    'https://www.linkedin.com/in/yeshaswini-k-p-0252b2131',
    'https://www.linkedin.com/in/atul-singh-1a7421104',
    'https://www.linkedin.com/in/yeshaswini-k-p-0252b2131/',
    'https://www.linkedin.com/in/atul-singh-1a7421104/'
)
AND r.status != 'deleted';