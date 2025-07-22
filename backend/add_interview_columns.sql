-- Add transcript_data column to interview_sessions table
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS transcript_data JSON;

-- Update the InterviewStatus enum type to include 'processing'
-- First check if the type exists and what values it has
SELECT enum_range(NULL::interviewstatus);

-- If 'processing' is not in the enum, we need to add it
-- This is more complex in PostgreSQL, so we'll do it safely:
-- 1. Create a new type
-- 2. Update the column
-- 3. Drop the old type

-- Only run these if 'processing' is not already in the enum:
/*
CREATE TYPE interviewstatus_new AS ENUM ('scheduled', 'in_progress', 'completed', 'cancelled', 'processing');
ALTER TABLE interview_sessions ALTER COLUMN status TYPE interviewstatus_new USING status::text::interviewstatus_new;
DROP TYPE interviewstatus;
ALTER TYPE interviewstatus_new RENAME TO interviewstatus;
*/