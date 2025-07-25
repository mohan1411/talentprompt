-- Fix for missing interview_category column in interview_sessions table
-- This script adds the missing column that's causing the SQL error

-- Check if the column exists and add it if it doesn't
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='interview_sessions' 
        AND column_name='interview_category'
    ) THEN
        ALTER TABLE interview_sessions 
        ADD COLUMN interview_category VARCHAR;
        
        RAISE NOTICE 'Column interview_category added successfully';
    ELSE
        RAISE NOTICE 'Column interview_category already exists';
    END IF;
END $$;

-- Also ensure the interview_type column exists (in case that's missing too)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='interview_sessions' 
        AND column_name='interview_type'
    ) THEN
        ALTER TABLE interview_sessions 
        ADD COLUMN interview_type VARCHAR;
        
        RAISE NOTICE 'Column interview_type added successfully';
    ELSE
        RAISE NOTICE 'Column interview_type already exists';
    END IF;
END $$;

-- Update the alembic version to mark this migration as complete
-- This prevents the migration from trying to run again
UPDATE alembic_version 
SET version_num = 'add_interview_mode_fields'
WHERE version_num = 'oauth_fields_migration';

-- If the above update didn't work (no rows updated), insert the version
INSERT INTO alembic_version (version_num)
SELECT 'add_interview_mode_fields'
WHERE NOT EXISTS (
    SELECT 1 FROM alembic_version 
    WHERE version_num = 'add_interview_mode_fields'
);