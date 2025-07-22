-- Migration script to fix interview_type data
-- This moves old interview_type values to interview_category and sets interview_type to NULL

-- First, ensure interview_category column exists
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS interview_category VARCHAR;

-- Copy existing interview_type values to interview_category
UPDATE interview_sessions 
SET interview_category = interview_type
WHERE interview_type IS NOT NULL 
  AND interview_type NOT IN ('IN_PERSON', 'VIRTUAL', 'PHONE');

-- Clear invalid interview_type values (they're now in interview_category)
UPDATE interview_sessions 
SET interview_type = NULL
WHERE interview_type IS NOT NULL 
  AND interview_type NOT IN ('IN_PERSON', 'VIRTUAL', 'PHONE');

-- Show results
SELECT 
    COUNT(*) as total_sessions,
    COUNT(interview_category) as sessions_with_category,
    COUNT(interview_type) as sessions_with_valid_type
FROM interview_sessions;