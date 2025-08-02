-- Check Michelle Garcia's pipeline state
SELECT 
    r.id as resume_id,
    r.first_name,
    r.last_name,
    cps.id as pipeline_state_id,
    cps.current_stage_id,
    cps.is_active,
    p.name as pipeline_name
FROM resumes r
JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id
JOIN pipelines p ON cps.pipeline_id = p.id
WHERE LOWER(r.first_name) = 'michelle' AND LOWER(r.last_name) = 'garcia';

-- Check if interview was created
SELECT 
    i.id,
    i.job_position,
    i.pipeline_state_id,
    i.status,
    i.created_at,
    r.first_name,
    r.last_name
FROM interview_sessions i
JOIN resumes r ON i.resume_id = r.id
WHERE LOWER(r.first_name) = 'michelle' AND LOWER(r.last_name) = 'garcia'
ORDER BY i.created_at DESC;

-- Check recent pipeline activities
SELECT 
    pa.activity_type,
    pa.from_stage_id,
    pa.to_stage_id,
    pa.details,
    pa.created_at
FROM pipeline_activities pa
JOIN resumes r ON pa.candidate_id = r.id
WHERE LOWER(r.first_name) = 'michelle' AND LOWER(r.last_name) = 'garcia'
ORDER BY pa.created_at DESC
LIMIT 5;