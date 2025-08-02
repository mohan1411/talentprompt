-- Move Michelle Garcia to Interview stage
UPDATE candidate_pipeline_states
SET 
    current_stage_id = 'interview',
    entered_stage_at = NOW(),
    updated_at = NOW()
WHERE candidate_id IN (
    SELECT id FROM resumes 
    WHERE LOWER(first_name) = 'michelle' AND LOWER(last_name) = 'garcia'
)
AND is_active = true;

-- Add activity log
INSERT INTO pipeline_activities (
    id,
    candidate_id,
    pipeline_state_id,
    user_id,
    activity_type,
    from_stage_id,
    to_stage_id,
    details,
    created_at
)
SELECT 
    gen_random_uuid(),
    r.id,
    cps.id,
    i.interviewer_id,
    'stage_changed',
    'screening',
    'interview',
    '{"reason": "Interview scheduled - moved to Interview stage"}',
    NOW()
FROM resumes r
JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id
JOIN interview_sessions i ON r.id = i.resume_id
WHERE LOWER(r.first_name) = 'michelle' AND LOWER(r.last_name) = 'garcia'
AND cps.is_active = true
ORDER BY i.created_at DESC
LIMIT 1;

-- Verify the update
SELECT 
    r.first_name,
    r.last_name,
    cps.current_stage_id,
    i.status as interview_status,
    i.pipeline_state_id
FROM resumes r
JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id
LEFT JOIN interview_sessions i ON r.id = i.resume_id
WHERE LOWER(r.first_name) = 'michelle' AND LOWER(r.last_name) = 'garcia'
AND cps.is_active = true
ORDER BY i.created_at DESC
LIMIT 1;