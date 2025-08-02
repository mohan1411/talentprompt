-- Check Donna Hall's current status and interview results
SELECT 
    r.first_name || ' ' || r.last_name as name,
    r.id as resume_id,
    cps.id as pipeline_state_id,
    cps.current_stage_id as current_stage,
    i.id as interview_id,
    i.overall_rating,
    i.recommendation,
    i.status as interview_status,
    i.pipeline_state_id as interview_pipeline_state_id
FROM resumes r
JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id
LEFT JOIN interview_sessions i ON r.id = i.resume_id
WHERE LOWER(r.first_name) = 'donna' 
AND LOWER(r.last_name) = 'hall'
AND cps.is_active = true
ORDER BY i.created_at DESC;

-- If Donna has a completed interview with rating >= 4 but is still in interview stage, 
-- run this to move her to offer stage:
UPDATE candidate_pipeline_states
SET 
    current_stage_id = 'offer',
    entered_stage_at = NOW(),
    updated_at = NOW()
WHERE candidate_id = (
    SELECT r.id 
    FROM resumes r
    WHERE LOWER(r.first_name) = 'donna' 
    AND LOWER(r.last_name) = 'hall'
    LIMIT 1
)
AND is_active = true
AND current_stage_id = 'interview'
AND EXISTS (
    SELECT 1 
    FROM interview_sessions i
    WHERE i.resume_id = candidate_id
    AND i.overall_rating >= 4
    AND i.status = 'completed'
);

-- Log the activity
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
    cps.candidate_id,
    cps.id,
    i.interviewer_id,
    'stage_changed',
    'interview',
    'offer',
    jsonb_build_object(
        'reason', 'Manual fix - Interview completed with rating ' || i.overall_rating || '/5',
        'interview_id', i.id::text,
        'interview_rating', i.overall_rating,
        'interview_recommendation', i.recommendation
    ),
    NOW()
FROM candidate_pipeline_states cps
JOIN interview_sessions i ON cps.candidate_id = i.resume_id
JOIN resumes r ON cps.candidate_id = r.id
WHERE LOWER(r.first_name) = 'donna' 
AND LOWER(r.last_name) = 'hall'
AND cps.is_active = true
AND cps.current_stage_id = 'offer'  -- Only log if we actually moved to offer
AND i.overall_rating >= 4
AND i.status = 'completed'
ORDER BY i.created_at DESC
LIMIT 1;