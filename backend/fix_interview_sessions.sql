-- Fix interview_sessions table - add missing columns

-- 1. Check current structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'interview_sessions'
AND column_name IN ('job_id', 'journey_id', 'pipeline_state_id', 'transcript_data', 'recordings', 'scorecard', 'strengths', 'concerns')
ORDER BY column_name;

-- 2. Add missing columns
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS job_id UUID REFERENCES jobs(id);

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS journey_id UUID REFERENCES candidate_journeys(id);

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS pipeline_state_id UUID REFERENCES candidate_pipeline_states(id);

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS transcript_data JSONB;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS recordings JSONB;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS scorecard JSONB;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS strengths JSONB;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS concerns JSONB;

-- 3. Verify the changes
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'interview_sessions'
AND column_name IN ('job_id', 'journey_id', 'pipeline_state_id')
ORDER BY column_name;