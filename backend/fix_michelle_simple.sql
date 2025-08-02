-- Simple fix for Michelle Garcia
-- This can be run separately after the trigger is created

-- Move Michelle to Interview stage
UPDATE candidate_pipeline_states
SET 
    current_stage_id = 'interview',
    entered_stage_at = NOW(),
    updated_at = NOW()
WHERE candidate_id = (
    SELECT id FROM resumes 
    WHERE LOWER(first_name) = 'michelle' 
    AND LOWER(last_name) = 'garcia'
    ORDER BY created_at DESC
    LIMIT 1
)
AND is_active = true
AND current_stage_id = 'screening';

-- Verify the update
SELECT 
    r.first_name || ' ' || r.last_name as name,
    cps.current_stage_id as current_stage,
    cps.updated_at as last_updated
FROM resumes r
JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id
WHERE LOWER(r.first_name) = 'michelle' 
AND LOWER(r.last_name) = 'garcia'
AND cps.is_active = true;