-- Fix for LOCAL database only - rename columns to match the model
-- DO NOT RUN IN PRODUCTION

-- Check if the column exists and rename it
DO $$
BEGIN
    -- Check if current_stage_id exists and current_stage doesn't
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'candidate_pipeline_states' 
        AND column_name = 'current_stage_id'
    ) AND NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'candidate_pipeline_states' 
        AND column_name = 'current_stage'
    ) THEN
        -- Rename the column
        ALTER TABLE candidate_pipeline_states 
        RENAME COLUMN current_stage_id TO current_stage;
        
        RAISE NOTICE 'Renamed current_stage_id to current_stage';
    ELSE
        RAISE NOTICE 'Column already correct or does not exist';
    END IF;
    
    -- Check if entered_stage_at exists and stage_entered_at doesn't
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'candidate_pipeline_states' 
        AND column_name = 'entered_stage_at'
    ) AND NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'candidate_pipeline_states' 
        AND column_name = 'stage_entered_at'
    ) THEN
        -- Rename the column
        ALTER TABLE candidate_pipeline_states 
        RENAME COLUMN entered_stage_at TO stage_entered_at;
        
        RAISE NOTICE 'Renamed entered_stage_at to stage_entered_at';
    ELSE
        RAISE NOTICE 'Column stage_entered_at already correct or does not exist';
    END IF;
END $$;

-- Also check pipeline_activities table
DO $$
BEGIN
    -- Fix from_stage_id to from_stage
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'pipeline_activities' 
        AND column_name = 'from_stage_id'
    ) AND NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'pipeline_activities' 
        AND column_name = 'from_stage'
    ) THEN
        ALTER TABLE pipeline_activities 
        RENAME COLUMN from_stage_id TO from_stage;
        
        RAISE NOTICE 'Renamed from_stage_id to from_stage';
    END IF;
    
    -- Fix to_stage_id to to_stage
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'pipeline_activities' 
        AND column_name = 'to_stage_id'
    ) AND NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'pipeline_activities' 
        AND column_name = 'to_stage'
    ) THEN
        ALTER TABLE pipeline_activities 
        RENAME COLUMN to_stage_id TO to_stage;
        
        RAISE NOTICE 'Renamed to_stage_id to to_stage';
    END IF;
    
    -- Fix user_id to performed_by
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'pipeline_activities' 
        AND column_name = 'user_id'
    ) AND NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'pipeline_activities' 
        AND column_name = 'performed_by'
    ) THEN
        ALTER TABLE pipeline_activities 
        RENAME COLUMN user_id TO performed_by;
        
        RAISE NOTICE 'Renamed user_id to performed_by';
    END IF;
END $$;

-- Show current columns to verify
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name IN ('candidate_pipeline_states', 'pipeline_activities')
AND column_name IN ('current_stage', 'current_stage_id', 'stage_entered_at', 'entered_stage_at', 
                    'from_stage', 'from_stage_id', 'to_stage', 'to_stage_id', 
                    'performed_by', 'user_id')
ORDER BY table_name, column_name;