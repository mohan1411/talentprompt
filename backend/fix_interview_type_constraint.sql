-- Fix interview_type constraint and migrate data properly

-- First, ensure interview_category column exists
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS interview_category VARCHAR;

-- Copy existing interview_type values to interview_category (if not already done)
UPDATE interview_sessions 
SET interview_category = interview_type
WHERE interview_category IS NULL 
  AND interview_type IS NOT NULL;

-- Now we need to handle the interview_type column
-- Option 1: Make it nullable first
ALTER TABLE interview_sessions ALTER COLUMN interview_type DROP NOT NULL;

-- Then set existing invalid values to NULL
UPDATE interview_sessions 
SET interview_type = NULL
WHERE interview_type IS NOT NULL 
  AND interview_type NOT IN ('IN_PERSON', 'VIRTUAL', 'PHONE');

-- Show results
SELECT 
    COUNT(*) as total_sessions,
    COUNT(interview_category) as sessions_with_category,
    COUNT(interview_type) as sessions_with_valid_type,
    COUNT(CASE WHEN interview_type IS NULL THEN 1 END) as sessions_without_type
FROM interview_sessions;