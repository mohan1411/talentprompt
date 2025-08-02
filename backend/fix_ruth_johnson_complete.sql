-- Fix Ruth Johnson's pipeline stage issue
-- Run each query separately in pgAdmin

-- 1. First, check Ruth's current status
SELECT 
    r.first_name || ' ' || r.last_name as name,
    r.id as resume_id,
    cps.id as pipeline_state_id,
    cps.current_stage_id,
    cps.entered_stage_at,
    i.id as interview_id,
    i.status as interview_status,
    i.overall_rating,
    i.recommendation,
    i.started_at,
    i.ended_at
FROM resumes r
LEFT JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id AND cps.is_active = true
LEFT JOIN interview_sessions i ON r.id = i.resume_id
WHERE LOWER(r.first_name) = 'ruth' 
AND LOWER(r.last_name) = 'johnson'
ORDER BY i.created_at DESC;

-- 2. If Ruth has a completed interview with rating >= 4, move her to offer
UPDATE candidate_pipeline_states
SET 
    current_stage_id = 'offer',
    entered_stage_at = NOW(),
    updated_at = NOW(),
    time_in_stage_seconds = EXTRACT(EPOCH FROM (NOW() - entered_stage_at))
WHERE id = (
    SELECT cps.id
    FROM candidate_pipeline_states cps
    JOIN resumes r ON cps.candidate_id = r.id
    WHERE LOWER(r.first_name) = 'ruth' 
    AND LOWER(r.last_name) = 'johnson'
    AND cps.is_active = true
    LIMIT 1
)
AND EXISTS (
    SELECT 1
    FROM interview_sessions i
    JOIN resumes r ON i.resume_id = r.id
    WHERE LOWER(r.first_name) = 'ruth' 
    AND LOWER(r.last_name) = 'johnson'
    AND i.overall_rating >= 4
    AND i.status = 'completed'
)
AND current_stage_id != 'offer';

-- 3. Create activity log for the stage change
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
    'interview',
    'offer',
    jsonb_build_object(
        'reason', 'Manual fix - Interview completed with rating ' || i.overall_rating || '/5',
        'interview_id', i.id::text,
        'interview_rating', i.overall_rating,
        'interview_recommendation', i.recommendation
    ),
    NOW()
FROM resumes r
JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id
JOIN interview_sessions i ON r.id = i.resume_id
WHERE LOWER(r.first_name) = 'ruth' 
AND LOWER(r.last_name) = 'johnson'
AND cps.is_active = true
AND cps.current_stage_id = 'offer'
AND i.overall_rating >= 4
AND i.status = 'completed'
AND NOT EXISTS (
    SELECT 1 FROM pipeline_activities pa
    WHERE pa.candidate_id = r.id
    AND pa.to_stage_id = 'offer'
    AND pa.created_at > NOW() - INTERVAL '1 minute'
)
ORDER BY i.created_at DESC
LIMIT 1;

-- 4. Verify the fix
SELECT 
    r.first_name || ' ' || r.last_name as name,
    cps.current_stage_id as current_stage,
    cps.updated_at,
    i.overall_rating,
    i.recommendation,
    CASE 
        WHEN cps.current_stage_id = 'offer' THEN 'FIXED - Now in Offer stage'
        WHEN cps.current_stage_id = 'interview' THEN 'STILL IN INTERVIEW - Check if interview is completed'
        ELSE 'In ' || cps.current_stage_id || ' stage'
    END as status
FROM resumes r
LEFT JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id AND cps.is_active = true
LEFT JOIN interview_sessions i ON r.id = i.resume_id AND i.status = 'completed'
WHERE LOWER(r.first_name) = 'ruth' 
AND LOWER(r.last_name) = 'johnson';