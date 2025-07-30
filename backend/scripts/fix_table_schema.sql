-- Fix table schema to match the model exactly

-- First, show current columns
SELECT 
    'CURRENT COLUMNS' as section,
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'candidate_submissions'
ORDER BY ordinal_position;

-- Add all missing columns from the model
ALTER TABLE candidate_submissions 
ADD COLUMN IF NOT EXISTS phone VARCHAR(50),
ADD COLUMN IF NOT EXISTS resume_file_url VARCHAR(500);

-- Verify all columns exist
SELECT 
    'AFTER ADDING COLUMNS' as section,
    COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name = 'candidate_submissions';

-- List all columns after update
SELECT 
    ordinal_position,
    column_name, 
    data_type, 
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'candidate_submissions'
ORDER BY ordinal_position;

-- Quick test to make sure table is working
INSERT INTO candidate_submissions (
    token, 
    submission_type, 
    status, 
    recruiter_id, 
    email, 
    expires_at
) VALUES (
    'test_' || gen_random_uuid()::text,
    'new',
    'pending',
    gen_random_uuid(),
    'test@example.com',
    CURRENT_TIMESTAMP + INTERVAL '7 days'
) RETURNING id, token;

-- Clean up test
DELETE FROM candidate_submissions WHERE email = 'test@example.com';

SELECT '✅ Table schema fixed and tested!' as result;