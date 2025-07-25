-- Quick fix for missing columns in interview_sessions table
-- Run this SQL directly in your PostgreSQL database

-- Add missing columns
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS interview_category VARCHAR;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS transcript_data JSON;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS journey_id UUID;

-- Optional: Set default values for existing records
-- UPDATE interview_sessions 
-- SET interview_category = 'general' 
-- WHERE interview_category IS NULL;