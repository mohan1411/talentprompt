-- Comprehensive fix for ALL missing columns in interview_sessions table
-- Run this SQL directly in your PostgreSQL database to fix all column errors

-- Add all potentially missing columns from the InterviewSession model
-- Each column is added only if it doesn't already exist

-- Basic session details
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS interview_category VARCHAR;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS interview_type VARCHAR;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS job_requirements JSON;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS duration_minutes INTEGER;

-- AI-generated content
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS preparation_notes JSON;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS suggested_questions JSON;

-- Interview data
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS transcript TEXT;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS transcript_data JSON;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS notes TEXT;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS recordings JSON;

-- Evaluation fields
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS scorecard JSON;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS overall_rating FLOAT;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS recommendation VARCHAR;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS strengths JSON;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS concerns JSON;

-- Pipeline journey tracking
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS journey_id UUID;

-- Add foreign key constraint for journey_id if the table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'candidate_journeys') THEN
        ALTER TABLE interview_sessions 
        ADD CONSTRAINT fk_interview_journey 
        FOREIGN KEY (journey_id) 
        REFERENCES candidate_journeys(id)
        ON DELETE SET NULL;
    END IF;
EXCEPTION
    WHEN duplicate_object THEN
        -- Constraint already exists
        NULL;
END $$;

-- Fix the status enum to include PROCESSING value
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
            ALTER TYPE interviewstatus ADD VALUE IF NOT EXISTS 'PROCESSING';
            RAISE NOTICE 'Added PROCESSING value to interviewstatus enum';
        END IF;
    END IF;
END $$;

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'All missing columns have been added to interview_sessions table';
    RAISE NOTICE 'InterviewStatus enum has been fixed with PROCESSING value';
END $$;