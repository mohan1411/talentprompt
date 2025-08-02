-- Fix tags column type from JSONB to TEXT[]
-- For LOCAL database only

-- Step 1: Rename the old tags column
ALTER TABLE candidate_pipeline_states 
RENAME COLUMN tags TO tags_jsonb;

-- Step 2: Add new tags column with correct type
ALTER TABLE candidate_pipeline_states 
ADD COLUMN tags TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Step 3: Migrate data from old column to new (if any exists)
UPDATE candidate_pipeline_states 
SET tags = CASE 
    WHEN tags_jsonb IS NULL THEN ARRAY[]::TEXT[]
    WHEN jsonb_typeof(tags_jsonb) = 'array' THEN 
        ARRAY(SELECT jsonb_array_elements_text(tags_jsonb))
    ELSE ARRAY[]::TEXT[]
END;

-- Step 4: Drop the old column
ALTER TABLE candidate_pipeline_states 
DROP COLUMN tags_jsonb;

-- Verify the change
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'candidate_pipeline_states'
AND column_name = 'tags';