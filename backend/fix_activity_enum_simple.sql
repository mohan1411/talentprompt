-- Simple fix for pipeline_activity_type enum

-- 1. Check what values currently exist
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'pipeline_activity_type')
ORDER BY enumsortorder;

-- 2. Drop the old type (this will cascade to any columns using it)
DROP TYPE IF EXISTS pipeline_activity_type CASCADE;

-- 3. Create with correct lowercase values
CREATE TYPE pipeline_activity_type AS ENUM (
    'moved',
    'noted', 
    'assigned',
    'tagged',
    'contacted',
    'evaluated'
);

-- 4. Re-add the column to pipeline_activities table if it exists
ALTER TABLE pipeline_activities 
ADD COLUMN IF NOT EXISTS activity_type pipeline_activity_type;

-- 5. Verify the result
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'pipeline_activity_type')
ORDER BY enumsortorder;