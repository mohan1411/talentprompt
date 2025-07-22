-- Fix local database for interview workflow changes

-- 1. Add interview_category column if it doesn't exist
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS interview_category VARCHAR;

-- 2. Copy existing interview_type values to interview_category
UPDATE interview_sessions 
SET interview_category = interview_type
WHERE interview_category IS NULL 
  AND interview_type IS NOT NULL;

-- 3. Make interview_type nullable (remove NOT NULL constraint)
ALTER TABLE interview_sessions ALTER COLUMN interview_type DROP NOT NULL;

-- 4. Clear invalid interview_type values
UPDATE interview_sessions 
SET interview_type = NULL
WHERE interview_type IS NOT NULL 
  AND interview_type NOT IN ('IN_PERSON', 'VIRTUAL', 'PHONE');

-- 5. Show results
SELECT 
    id,
    job_position,
    interview_type,
    interview_category,
    status
FROM interview_sessions
ORDER BY created_at DESC;