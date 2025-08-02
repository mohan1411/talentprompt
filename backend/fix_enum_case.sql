-- Check and fix the interviewstatus enum values
-- The application expects UPPERCASE but database might have lowercase

-- First, let's check what values exist
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'interviewstatus')
ORDER BY enumsortorder;

-- If the values are lowercase, we need to recreate the enum with UPPERCASE values
-- This is a destructive operation, so we need to:
-- 1. Create a new enum with correct values
-- 2. Update the column to use the new enum
-- 3. Drop the old enum

BEGIN;

-- Create new enum with UPPERCASE values
CREATE TYPE interviewstatus_new AS ENUM ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'PROCESSING');

-- Convert the column to text temporarily
ALTER TABLE interview_sessions 
ALTER COLUMN status TYPE text;

-- Update any lowercase values to uppercase
UPDATE interview_sessions 
SET status = UPPER(status)
WHERE status IS NOT NULL;

-- Drop the old enum
DROP TYPE IF EXISTS interviewstatus CASCADE;

-- Rename the new enum
ALTER TYPE interviewstatus_new RENAME TO interviewstatus;

-- Convert the column back to enum
ALTER TABLE interview_sessions 
ALTER COLUMN status TYPE interviewstatus 
USING status::interviewstatus;

-- Set default
ALTER TABLE interview_sessions 
ALTER COLUMN status SET DEFAULT 'SCHEDULED'::interviewstatus;

COMMIT;

-- Verify the result
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'interviewstatus')
ORDER BY enumsortorder;