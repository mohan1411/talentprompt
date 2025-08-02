-- RUN EACH STATEMENT SEPARATELY IN PGADMIN

-- Statement 1: Move Michelle to Interview stage
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
AND current_stage_id != 'interview';

-- Statement 2: Check Michelle's current status
SELECT 
    r.first_name || ' ' || r.last_name as name,
    cps.current_stage_id as current_stage,
    cps.updated_at
FROM resumes r
JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id
WHERE LOWER(r.first_name) = 'michelle' 
AND LOWER(r.last_name) = 'garcia'
AND cps.is_active = true;

-- Statement 3: Fix ALL candidates who have interviews but are still in screening
UPDATE candidate_pipeline_states cps
SET 
    current_stage_id = 'interview',
    entered_stage_at = NOW(),
    updated_at = NOW()
FROM interview_sessions i
WHERE cps.candidate_id = i.resume_id
AND cps.is_active = true
AND cps.current_stage_id = 'screening'
AND i.pipeline_state_id IS NOT NULL;

-- Statement 4: See which candidates were updated
SELECT 
    r.first_name || ' ' || r.last_name as candidate_name,
    cps.current_stage_id as current_stage,
    i.created_at as interview_created
FROM candidate_pipeline_states cps
JOIN resumes r ON cps.candidate_id = r.id
JOIN interview_sessions i ON r.id = i.resume_id
WHERE cps.is_active = true
AND i.pipeline_state_id IS NOT NULL
ORDER BY i.created_at DESC;