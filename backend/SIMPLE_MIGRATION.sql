-- Simple migration to add candidate_id to interview_sessions
-- Run this on your production database

-- Step 1: Add candidate_id column if it doesn't exist
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS candidate_id UUID;

-- Step 2: Add job_id column if it doesn't exist (required by model)
ALTER TABLE interview_sessions
ADD COLUMN IF NOT EXISTS job_id UUID;

-- That's it! The application will now work with both fields.
-- The full migration to populate candidate_id can be done later.