-- Fix foreign key constraint for candidate_pipeline_states
-- The candidate_id should reference candidates.id, not resumes.id

-- Step 1: Check current foreign key constraints
SELECT 
    conname AS constraint_name,
    conrelid::regclass AS table_name,
    confrelid::regclass AS foreign_table_name
FROM pg_constraint
WHERE conrelid = 'candidate_pipeline_states'::regclass
AND contype = 'f';

-- Step 2: Drop the incorrect foreign key constraint
ALTER TABLE candidate_pipeline_states
DROP CONSTRAINT IF EXISTS candidate_pipeline_states_candidate_id_fkey;

-- Step 3: Add the correct foreign key constraint to candidates table
ALTER TABLE candidate_pipeline_states
ADD CONSTRAINT candidate_pipeline_states_candidate_id_fkey 
FOREIGN KEY (candidate_id) 
REFERENCES candidates(id) 
ON DELETE CASCADE;

-- Step 4: Verify the change
SELECT 
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
AND tc.table_name='candidate_pipeline_states'
AND kcu.column_name = 'candidate_id';