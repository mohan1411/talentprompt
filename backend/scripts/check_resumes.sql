-- Check resumes for promtitude@gmail.com
-- Run this with: psql -U promtitude -d promtitude -h localhost -p 5433 -f check_resumes.sql

\echo '========================================='
\echo 'RESUME DATABASE CHECK'
\echo '========================================='

-- Find the user
\echo '\n1. Finding user promtitude@gmail.com:'
SELECT id, email, full_name, is_active, created_at 
FROM users 
WHERE email = 'promtitude@gmail.com';

-- Store user ID in a variable (you might need to manually note this)
\echo '\n2. Counting resumes for this user:'
SELECT COUNT(*) as resume_count
FROM resumes r
JOIN users u ON r.user_id = u.id
WHERE u.email = 'promtitude@gmail.com';

-- Show sample resumes
\echo '\n3. Sample resumes for promtitude@gmail.com:'
SELECT r.id, r.first_name, r.last_name, r.current_title, r.status, r.created_at
FROM resumes r
JOIN users u ON r.user_id = u.id
WHERE u.email = 'promtitude@gmail.com'
ORDER BY r.created_at DESC
LIMIT 10;

-- Check total resumes in system
\echo '\n4. Total resumes in database:'
SELECT COUNT(*) as total_resumes FROM resumes;

-- Check which users have resumes
\echo '\n5. Users with resumes:'
SELECT u.email, COUNT(r.id) as resume_count
FROM users u
LEFT JOIN resumes r ON u.id = r.user_id
GROUP BY u.id, u.email
HAVING COUNT(r.id) > 0
ORDER BY resume_count DESC;

-- Check if there are any orphaned resumes
\echo '\n6. Checking for orphaned resumes (no valid user):'
SELECT COUNT(*) as orphaned_count
FROM resumes r
LEFT JOIN users u ON r.user_id = u.id
WHERE u.id IS NULL;

-- Get the exact user_id for promtitude@gmail.com
\echo '\n7. IMPORTANT - Copy this user ID for promtitude@gmail.com:'
SELECT id FROM users WHERE email = 'promtitude@gmail.com';