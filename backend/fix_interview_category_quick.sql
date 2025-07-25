-- Quick fix for missing interview_category column
-- Run this SQL directly in your PostgreSQL database

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS interview_category VARCHAR;

-- Optional: Set default values for existing records
-- UPDATE interview_sessions 
-- SET interview_category = 'general' 
-- WHERE interview_category IS NULL;