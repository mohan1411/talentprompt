-- Fix the unique constraint to only apply when is_default is true
-- This allows multiple non-default pipelines per team

-- Drop the existing constraint
ALTER TABLE pipelines DROP CONSTRAINT IF EXISTS unique_default_pipeline_per_team;

-- Add a new constraint that only enforces uniqueness for default pipelines
-- Using a partial unique index instead of a constraint
CREATE UNIQUE INDEX unique_default_pipeline_per_team 
ON pipelines (team_id) 
WHERE is_default = true;

-- Also create a unique index for global default pipeline (when team_id is NULL)
CREATE UNIQUE INDEX unique_global_default_pipeline 
ON pipelines ((1)) 
WHERE team_id IS NULL AND is_default = true;

-- This allows:
-- 1. Multiple non-default pipelines per team
-- 2. Multiple non-default global pipelines (team_id = NULL)
-- 3. Only one default pipeline per team
-- 4. Only one global default pipeline