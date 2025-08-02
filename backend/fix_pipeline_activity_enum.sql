-- Fix pipeline_activity_type enum values in LOCAL database

-- 1. First, check what values currently exist in the enum
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'pipeline_activity_type')
ORDER BY enumsortorder;

-- 2. Drop and recreate the enum with correct values
-- The model expects: moved, noted, assigned, tagged, contacted, evaluated

BEGIN;

-- Create new enum with correct values (lowercase)
CREATE TYPE pipeline_activity_type_new AS ENUM (
    'moved',
    'noted', 
    'assigned',
    'tagged',
    'contacted',
    'evaluated'
);

-- If pipeline_activities table exists, update it
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'pipeline_activities'
    ) THEN
        -- Temporarily change column to text
        ALTER TABLE pipeline_activities 
        ALTER COLUMN activity_type TYPE text;
        
        -- Map any old values to new ones (adjust as needed)
        UPDATE pipeline_activities 
        SET activity_type = LOWER(activity_type)
        WHERE activity_type IS NOT NULL;
        
        -- Update any specific mappings if needed
        UPDATE pipeline_activities 
        SET activity_type = 'moved' 
        WHERE activity_type IN ('stage_changed', 'STAGE_CHANGED', 'MOVED');
        
        UPDATE pipeline_activities 
        SET activity_type = 'noted' 
        WHERE activity_type IN ('comment_added', 'COMMENT_ADDED', 'NOTED', 'note_added');
    END IF;
END $$;

-- Drop old enum type
DROP TYPE IF EXISTS pipeline_activity_type CASCADE;

-- Rename new to old
ALTER TYPE pipeline_activity_type_new RENAME TO pipeline_activity_type;

-- If pipeline_activities table exists, change column back to enum
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'pipeline_activities'
    ) THEN
        ALTER TABLE pipeline_activities 
        ALTER COLUMN activity_type TYPE pipeline_activity_type 
        USING activity_type::pipeline_activity_type;
    END IF;
END $$;

COMMIT;

-- 3. Verify the result
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'pipeline_activity_type')
ORDER BY enumsortorder;