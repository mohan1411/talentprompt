-- Create the interviewmode enum type in the database

-- First, check if the type already exists and drop it if needed
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'interviewmode') THEN
        DROP TYPE interviewmode CASCADE;
    END IF;
END $$;

-- Create the enum type
CREATE TYPE interviewmode AS ENUM ('IN_PERSON', 'VIRTUAL', 'PHONE');

-- Now we need to alter the interview_type column to use this enum
-- First, ensure it's nullable (we already did this)
ALTER TABLE interview_sessions ALTER COLUMN interview_type DROP NOT NULL;

-- Convert the column to use the enum type
ALTER TABLE interview_sessions 
    ALTER COLUMN interview_type TYPE interviewmode 
    USING NULL;  -- Set all existing values to NULL since they don't match the enum

-- Verify the changes
\d interview_sessions