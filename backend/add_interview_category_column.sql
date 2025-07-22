-- Add interview_category column to interview_sessions table
-- Run this script on your production database

-- Check if column exists first
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'interview_sessions' 
        AND column_name = 'interview_category'
    ) THEN
        ALTER TABLE interview_sessions ADD COLUMN interview_category VARCHAR;
        RAISE NOTICE 'interview_category column added successfully';
    ELSE
        RAISE NOTICE 'interview_category column already exists';
    END IF;
END $$;