-- Manual fix for Brian Williams pipeline issue

-- 1. Find Brian Williams' IDs
SELECT 
    r.id as resume_id,
    r.first_name,
    r.last_name,
    cps.id as pipeline_state_id,
    cps.current_stage_id,
    cps.pipeline_id,
    p.name as pipeline_name
FROM resumes r
JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id
JOIN pipelines p ON cps.pipeline_id = p.id
WHERE LOWER(r.first_name) = 'brian' AND LOWER(r.last_name) = 'williams';

-- 2. Link existing interviews to pipeline (replace IDs from query above)
UPDATE interview_sessions 
SET pipeline_state_id = (
    SELECT cps.id 
    FROM candidate_pipeline_states cps
    JOIN resumes r ON cps.candidate_id = r.id
    WHERE LOWER(r.first_name) = 'brian' AND LOWER(r.last_name) = 'williams'
    AND cps.is_active = true
    LIMIT 1
)
WHERE resume_id = (
    SELECT id FROM resumes 
    WHERE LOWER(first_name) = 'brian' AND LOWER(last_name) = 'williams'
    LIMIT 1
)
AND pipeline_state_id IS NULL;

-- 3. Move Brian to Interview stage
UPDATE candidate_pipeline_states
SET 
    current_stage_id = 'interview',
    entered_stage_at = NOW(),
    updated_at = NOW()
WHERE candidate_id = (
    SELECT id FROM resumes 
    WHERE LOWER(first_name) = 'brian' AND LOWER(last_name) = 'williams'
    LIMIT 1
)
AND is_active = true;

-- 4. Log the activity
INSERT INTO pipeline_activities (
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
    cps.candidate_id,
    cps.id,
    cps.updated_by,
    'stage_changed',
    'screening',
    'interview',
    '{"reason": "Manual fix - Interview scheduled"}',
    NOW()
FROM candidate_pipeline_states cps
JOIN resumes r ON cps.candidate_id = r.id
WHERE LOWER(r.first_name) = 'brian' AND LOWER(r.last_name) = 'williams'
AND cps.is_active = true;

-- 5. Verify the fix
SELECT 
    r.first_name,
    r.last_name,
    cps.current_stage_id,
    i.pipeline_state_id as interview_pipeline_link,
    i.status as interview_status
FROM resumes r
LEFT JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id AND cps.is_active = true
LEFT JOIN interview_sessions i ON r.id = i.resume_id
WHERE LOWER(r.first_name) = 'brian' AND LOWER(r.last_name) = 'williams';