-- Simulate exactly what happens when you try to import

-- 1. Your user details
SELECT 'YOUR USER:' as info;
SELECT id, email FROM users WHERE email = 'mohan.g1411@gmail.com';

-- 2. Check what the backend duplicate check would find
SELECT 'BACKEND DUPLICATE CHECK WOULD FIND:' as info;
SELECT 
    r.id,
    r.user_id,
    u.email,
    r.linkedin_url,
    r.status
FROM resumes r
JOIN users u ON r.user_id = u.id
WHERE r.linkedin_url IN (
    'https://www.linkedin.com/in/yeshaswini-k-p-0252b2131',
    'https://www.linkedin.com/in/atul-singh-1a7421104'
)
AND r.user_id = 'd48c0d47-d6d3-404b-9f58-8552534f9b4d'  -- your user_id
AND r.status != 'deleted';

-- 3. Try to simulate an insert
SELECT 'SIMULATING INSERT:' as info;
BEGIN;
-- Try to insert (we'll rollback so it won't actually save)
INSERT INTO resumes (
    user_id, 
    first_name, 
    last_name, 
    linkedin_url, 
    email,
    status,
    years_experience,
    created_at,
    updated_at
) VALUES (
    'd48c0d47-d6d3-404b-9f58-8552534f9b4d',
    'Test',
    'Profile',
    'https://www.linkedin.com/in/yeshaswini-k-p-0252b2131',
    'test@example.com',
    'active',
    0,
    NOW(),
    NOW()
);
-- If this fails, we'll see the exact error
ROLLBACK;

-- 4. List ALL constraints that could block this
SELECT 'CONSTRAINTS THAT COULD BLOCK:' as info;
SELECT 
    conname,
    pg_get_constraintdef(oid) as definition
FROM pg_constraint
WHERE conrelid = 'resumes'::regclass
AND (
    conname LIKE '%linkedin%'
    OR pg_get_constraintdef(oid) LIKE '%linkedin_url%'
);