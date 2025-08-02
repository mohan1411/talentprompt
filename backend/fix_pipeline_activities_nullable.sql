-- Fix pipeline_activities table - make candidate_id nullable
-- The Python model doesn't use candidate_id, it uses pipeline_state_id

-- 1. Check current structure
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'pipeline_activities'
ORDER BY ordinal_position;

-- 2. Make candidate_id nullable (if it exists)
ALTER TABLE pipeline_activities 
ALTER COLUMN candidate_id DROP NOT NULL;

-- 3. Verify the change
SELECT 
    column_name,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'pipeline_activities'
AND column_name = 'candidate_id';