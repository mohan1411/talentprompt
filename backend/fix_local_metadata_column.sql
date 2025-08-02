-- Fix for LOCAL database only - add missing metadata column
-- DO NOT RUN IN PRODUCTION

-- Add metadata column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'candidate_pipeline_states' 
        AND column_name = 'metadata'
    ) THEN
        ALTER TABLE candidate_pipeline_states 
        ADD COLUMN metadata JSONB DEFAULT '{}';
        
        RAISE NOTICE 'Added metadata column to candidate_pipeline_states';
    ELSE
        RAISE NOTICE 'metadata column already exists';
    END IF;
END $$;

-- Also check and add any other potentially missing columns
DO $$
BEGIN
    -- Add tags column if missing
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'candidate_pipeline_states' 
        AND column_name = 'tags'
    ) THEN
        ALTER TABLE candidate_pipeline_states 
        ADD COLUMN tags TEXT[] DEFAULT ARRAY[]::TEXT[];
        
        RAISE NOTICE 'Added tags column to candidate_pipeline_states';
    END IF;
    
    -- Add updated_at column if missing
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'candidate_pipeline_states' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE candidate_pipeline_states 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        RAISE NOTICE 'Added updated_at column to candidate_pipeline_states';
    END IF;
    
    -- Add created_at column if missing
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'candidate_pipeline_states' 
        AND column_name = 'created_at'
    ) THEN
        ALTER TABLE candidate_pipeline_states 
        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        RAISE NOTICE 'Added created_at column to candidate_pipeline_states';
    END IF;
END $$;

-- Show all columns in candidate_pipeline_states to verify
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'candidate_pipeline_states'
ORDER BY ordinal_position;