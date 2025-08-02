-- =====================================================
-- INTERVIEW SESSION MIGRATION
-- Migrates interview_sessions from resume_id to candidate_id
-- =====================================================

-- Step 1: Add candidate_id column if it doesn't exist
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS candidate_id UUID REFERENCES candidates(id);

-- Step 2: Create candidates for existing resumes that are in interview_sessions
INSERT INTO candidates (id, resume_id, first_name, last_name, email, phone, current_title, location, skills, years_of_experience, created_at, updated_at)
SELECT 
    gen_random_uuid() as id,
    r.id as resume_id,
    r.first_name,
    r.last_name,
    r.email,
    r.phone,
    r.current_title,
    r.location,
    r.skills,
    CASE 
        WHEN r.years_experience ~ '^\d+(\.\d+)?$' THEN r.years_experience::float
        ELSE NULL
    END as years_of_experience,
    NOW() as created_at,
    NOW() as updated_at
FROM resumes r
WHERE r.id IN (
    SELECT DISTINCT resume_id 
    FROM interview_sessions 
    WHERE resume_id IS NOT NULL
)
AND NOT EXISTS (
    SELECT 1 FROM candidates c WHERE c.resume_id = r.id
);

-- Step 3: Update interview_sessions to set candidate_id based on resume_id
UPDATE interview_sessions is_table
SET candidate_id = c.id
FROM candidates c
WHERE is_table.resume_id = c.resume_id
AND is_table.candidate_id IS NULL;

-- Step 4: Add job_id column if it doesn't exist (required by the model)
ALTER TABLE interview_sessions
ADD COLUMN IF NOT EXISTS job_id UUID REFERENCES jobs(id);

-- Step 5: Drop the old resume_id column (optional - only if you're sure)
-- ALTER TABLE interview_sessions DROP COLUMN resume_id;

-- Step 6: Make candidate_id NOT NULL after migration (optional - only after ensuring all records have candidate_id)
-- ALTER TABLE interview_sessions ALTER COLUMN candidate_id SET NOT NULL;

-- Verify the migration
SELECT 
    COUNT(*) as total_sessions,
    COUNT(candidate_id) as sessions_with_candidate,
    COUNT(resume_id) as sessions_with_resume
FROM interview_sessions;