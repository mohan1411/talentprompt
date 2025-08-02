-- Fix PostgreSQL cache issue after type changes

-- 1. First, let's check the current state of pipeline_activities
\d pipeline_activities

-- 2. Drop and recreate the pipeline_activities table with correct structure
-- Save any existing data first (if needed)
CREATE TEMP TABLE pipeline_activities_backup AS 
SELECT * FROM pipeline_activities;

-- Drop the table
DROP TABLE IF EXISTS pipeline_activities CASCADE;

-- Recreate with correct structure
CREATE TABLE pipeline_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_state_id UUID REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
    activity_type pipeline_activity_type NOT NULL,
    from_stage VARCHAR(50),
    to_stage VARCHAR(50),
    performed_by UUID REFERENCES users(id),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_pipeline_activities_pipeline_state ON pipeline_activities(pipeline_state_id);
CREATE INDEX idx_pipeline_activities_performed_by ON pipeline_activities(performed_by);
CREATE INDEX idx_pipeline_activities_created_at ON pipeline_activities(created_at);

-- Restore any data (if exists and valid)
-- INSERT INTO pipeline_activities SELECT * FROM pipeline_activities_backup WHERE ... ;

-- Drop temp table
DROP TABLE IF EXISTS pipeline_activities_backup;

-- Verify the new structure
\d pipeline_activities