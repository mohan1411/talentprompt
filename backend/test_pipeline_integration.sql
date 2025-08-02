-- Test if the interview has pipeline_state_id set
SELECT 
    i.id,
    i.resume_id,
    i.pipeline_state_id,
    i.status,
    i.created_at,
    r.first_name,
    r.last_name,
    cps.id as actual_pipeline_state_id,
    cps.current_stage_id
FROM interview_sessions i
JOIN resumes r ON i.resume_id = r.id
LEFT JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id AND cps.is_active = true
WHERE i.created_at > NOW() - INTERVAL '1 hour'
ORDER BY i.created_at DESC;

-- Check if pipeline activities are being created
SELECT * FROM pipeline_activities 
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;