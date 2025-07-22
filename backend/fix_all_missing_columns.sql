-- Fix all missing columns in the database

-- 1. Fix users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email_verification_sent_at TIMESTAMP WITH TIME ZONE;

-- 2. Fix interview_sessions table
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS interviewer_id UUID;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS transcript_data JSON;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS recordings JSON;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS journey_id UUID;

-- Add foreign key constraint for interviewer_id (references users table)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'interview_sessions_interviewer_id_fkey'
    ) THEN
        ALTER TABLE interview_sessions 
        ADD CONSTRAINT interview_sessions_interviewer_id_fkey 
        FOREIGN KEY (interviewer_id) REFERENCES users(id);
    END IF;
END $$;

-- 3. Check and update InterviewStatus enum if needed
DO $$ 
BEGIN
    -- Check if 'processing' exists in the enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'processing' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'interviewstatus')
    ) THEN
        -- Add 'processing' to the enum
        ALTER TYPE interviewstatus ADD VALUE IF NOT EXISTS 'processing';
    END IF;
END $$;

-- 4. Verify all columns exist
SELECT 
    'users' as table_name,
    column_name,
    data_type
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('email_verification_token', 'email_verification_sent_at')
UNION ALL
SELECT 
    'interview_sessions' as table_name,
    column_name,
    data_type
FROM information_schema.columns 
WHERE table_name = 'interview_sessions' 
AND column_name IN ('interviewer_id', 'transcript_data', 'recordings', 'journey_id')
ORDER BY table_name, column_name;

-- 5. Show current interview_sessions columns (for debugging)
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'interview_sessions'
ORDER BY ordinal_position;