-- Add missing resume_file_url column to candidate_submissions table

-- Check if column exists
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'candidate_submissions' 
AND column_name = 'resume_file_url';

-- Add the column if it doesn't exist
ALTER TABLE candidate_submissions 
ADD COLUMN IF NOT EXISTS resume_file_url VARCHAR(500);

-- Verify column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'candidate_submissions' 
AND column_name = 'resume_file_url';

-- Show all columns in the table
SELECT 
    column_name, 
    data_type, 
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'candidate_submissions'
ORDER BY ordinal_position;