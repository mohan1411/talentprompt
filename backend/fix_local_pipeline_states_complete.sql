-- Complete fix for LOCAL candidate_pipeline_states table
-- This aligns the local schema with what the Python model expects

-- 1. Add metadata column (the model expects this)
ALTER TABLE candidate_pipeline_states 
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- 2. Fix tags column type (model expects TEXT[], you have JSONB)
DO $$
BEGIN
    -- Check if tags is JSONB and needs conversion
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'candidate_pipeline_states' 
        AND column_name = 'tags'
        AND data_type = 'jsonb'
    ) THEN
        -- First rename old column
        ALTER TABLE candidate_pipeline_states 
        RENAME COLUMN tags TO tags_old;
        
        -- Add new column with correct type
        ALTER TABLE candidate_pipeline_states 
        ADD COLUMN tags TEXT[] DEFAULT ARRAY[]::TEXT[];
        
        -- Try to migrate data (if tags_old contains array data)
        UPDATE candidate_pipeline_states 
        SET tags = ARRAY(SELECT jsonb_array_elements_text(tags_old))
        WHERE tags_old IS NOT NULL 
        AND jsonb_typeof(tags_old) = 'array';
        
        -- Drop old column
        ALTER TABLE candidate_pipeline_states 
        DROP COLUMN tags_old;
        
        RAISE NOTICE 'Converted tags from JSONB to TEXT[]';
    END IF;
END $$;

-- 3. Ensure all required columns exist with correct types
ALTER TABLE candidate_pipeline_states 
ADD COLUMN IF NOT EXISTS assigned_to UUID;

ALTER TABLE candidate_pipeline_states 
ADD COLUMN IF NOT EXISTS stage_entered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE candidate_pipeline_states 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE candidate_pipeline_states 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- 4. If you have data in stage_entered_at but it's the wrong timezone type, copy it
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'candidate_pipeline_states' 
        AND column_name = 'stage_entered_at'
        AND data_type = 'timestamp without time zone'
    ) THEN
        -- Create temporary column
        ALTER TABLE candidate_pipeline_states 
        ADD COLUMN IF NOT EXISTS stage_entered_at_temp TIMESTAMP WITH TIME ZONE;
        
        -- Copy data
        UPDATE candidate_pipeline_states 
        SET stage_entered_at_temp = stage_entered_at::TIMESTAMP WITH TIME ZONE;
        
        -- Drop old and rename
        ALTER TABLE candidate_pipeline_states DROP COLUMN stage_entered_at;
        ALTER TABLE candidate_pipeline_states RENAME COLUMN stage_entered_at_temp TO stage_entered_at;
        
        RAISE NOTICE 'Fixed stage_entered_at timezone type';
    END IF;
END $$;

-- 5. Show final structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'candidate_pipeline_states'
AND column_name IN ('id', 'candidate_id', 'pipeline_id', 'current_stage', 
                    'stage_entered_at', 'assigned_to', 'tags', 'metadata', 
                    'created_at', 'updated_at')
ORDER BY 
    CASE column_name
        WHEN 'id' THEN 1
        WHEN 'candidate_id' THEN 2
        WHEN 'pipeline_id' THEN 3
        WHEN 'current_stage' THEN 4
        WHEN 'stage_entered_at' THEN 5
        WHEN 'assigned_to' THEN 6
        WHEN 'tags' THEN 7
        WHEN 'metadata' THEN 8
        WHEN 'created_at' THEN 9
        WHEN 'updated_at' THEN 10
    END;