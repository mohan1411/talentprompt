-- Fix InterviewStatus enum to include PROCESSING value
-- This fixes the error: invalid input value for enum interviewstatus: "PROCESSING"

-- First, check if the enum type exists and what values it has
DO $$
DECLARE
    enum_exists boolean;
    has_processing boolean;
BEGIN
    -- Check if enum type exists
    SELECT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'interviewstatus'
    ) INTO enum_exists;
    
    IF NOT enum_exists THEN
        -- Create the enum type with all values
        CREATE TYPE interviewstatus AS ENUM (
            'SCHEDULED',
            'IN_PROGRESS',
            'COMPLETED',
            'CANCELLED',
            'PROCESSING'
        );
        RAISE NOTICE 'Created interviewstatus enum type with all values';
    ELSE
        -- Check if PROCESSING value exists
        SELECT EXISTS (
            SELECT 1 FROM pg_enum 
            WHERE enumtypid = 'interviewstatus'::regtype 
            AND enumlabel = 'PROCESSING'
        ) INTO has_processing;
        
        IF NOT has_processing THEN
            -- Add PROCESSING to existing enum
            -- Note: This requires PostgreSQL 9.1+
            ALTER TYPE interviewstatus ADD VALUE IF NOT EXISTS 'PROCESSING';
            RAISE NOTICE 'Added PROCESSING value to interviewstatus enum';
        ELSE
            RAISE NOTICE 'PROCESSING value already exists in interviewstatus enum';
        END IF;
    END IF;
END $$;

-- Now update the column to use the enum type if it's not already
DO $$
DECLARE
    current_type text;
BEGIN
    -- Get current column type
    SELECT data_type INTO current_type
    FROM information_schema.columns
    WHERE table_name = 'interview_sessions' 
    AND column_name = 'status';
    
    IF current_type != 'USER-DEFINED' THEN
        -- First, ensure all existing values are valid enum values
        UPDATE interview_sessions 
        SET status = 'SCHEDULED' 
        WHERE status IS NULL OR status NOT IN ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'PROCESSING');
        
        -- Convert column to use enum type
        ALTER TABLE interview_sessions 
        ALTER COLUMN status TYPE interviewstatus 
        USING status::interviewstatus;
        
        RAISE NOTICE 'Converted status column to use interviewstatus enum type';
    ELSE
        RAISE NOTICE 'Status column already uses enum type';
    END IF;
END $$;

-- Set default value for status column
ALTER TABLE interview_sessions 
ALTER COLUMN status SET DEFAULT 'SCHEDULED'::interviewstatus;

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'InterviewStatus enum has been fixed. PROCESSING status is now available.';
END $$;