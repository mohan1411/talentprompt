-- Investigate the duplicate profiles issue
-- Check which users have imported these specific profiles

-- 1. Find all resumes for these LinkedIn URLs
SELECT 
    r.id as resume_id,
    r.user_id,
    u.email as user_email,
    r.first_name,
    r.last_name,
    r.linkedin_url,
    r.created_at,
    r.status
FROM resumes r
JOIN users u ON r.user_id = u.id
WHERE r.linkedin_url IN (
    'https://www.linkedin.com/in/yeshaswini-k-p-0252b2131',
    'https://www.linkedin.com/in/ravikant-kumar-347a8024',
    'https://www.linkedin.com/in/atul-singh-1a7421104'
)
ORDER BY r.linkedin_url, r.created_at;

-- 2. Get your current user ID (replace 'your-email@example.com' with your actual email)
-- SELECT id, email FROM users WHERE email = 'your-email@example.com';

-- 3. Check if these profiles exist for ANY user
SELECT 
    linkedin_url,
    COUNT(*) as import_count,
    COUNT(DISTINCT user_id) as unique_users,
    array_agg(DISTINCT user_id) as user_ids
FROM resumes
WHERE linkedin_url IN (
    'https://www.linkedin.com/in/yeshaswini-k-p-0252b2131',
    'https://www.linkedin.com/in/ravikant-kumar-347a8024',
    'https://www.linkedin.com/in/atul-singh-1a7421104'
)
GROUP BY linkedin_url;

-- 4. Check if URL normalization might be an issue (with/without trailing slash)
SELECT 
    linkedin_url,
    user_id,
    first_name,
    last_name
FROM resumes
WHERE linkedin_url LIKE '%yeshaswini-k-p%'
   OR linkedin_url LIKE '%ravikant-kumar%'
   OR linkedin_url LIKE '%atul-singh%';