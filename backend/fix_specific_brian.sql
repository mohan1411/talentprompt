-- Fix for the specific Brian Williams (the one in the pipeline)
-- Using ID: 912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5

-- 1. Check current status
SELECT 
    i.id as interview_id,
    i.resume_id,
    i.job_position,
    i.status,
    i.overall_rating,
    i.recommendation,
    i.pipeline_state_id,
    i.created_at,
    r.first_name,
    r.last_name,
    cps.id as current_pipeline_state_id,
    cps.current_stage_id as pipeline_stage
FROM resumes r
LEFT JOIN interview_sessions i ON r.id = i.resume_id
LEFT JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id AND cps.is_active = true
WHERE r.id = '912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5'
ORDER BY i.created_at DESC;

-- 2. Update the most recent interview to completed with hire recommendation
UPDATE interview_sessions 
SET 
    status = 'COMPLETED',
    overall_rating = 4.3,
    recommendation = 'hire',
    ended_at = NOW(),
    updated_at = NOW()
WHERE resume_id = '912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5'
AND status != 'COMPLETED'
ORDER BY created_at DESC
LIMIT 1;

-- 3. Move Brian to Offer stage
UPDATE candidate_pipeline_states
SET 
    current_stage_id = 'offer',
    entered_stage_at = NOW(),
    updated_at = NOW()
WHERE candidate_id = '912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5'
AND is_active = true;

-- 4. Add pipeline activity for the stage change
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
    '912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5',
    cps.id,
    i.interviewer_id,
    'stage_changed',
    'interview',
    'offer',
    '{"reason": "Interview completed with hire recommendation, rating: 4.3"}',
    NOW()
FROM candidate_pipeline_states cps
JOIN interview_sessions i ON i.resume_id = cps.candidate_id
WHERE cps.candidate_id = '912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5'
AND cps.is_active = true
ORDER BY i.created_at DESC
LIMIT 1;

-- 5. Verify the update
SELECT 
    r.id,
    r.first_name,
    r.last_name,
    cps.current_stage_id as current_pipeline_stage,
    i.status as interview_status,
    i.overall_rating,
    i.recommendation,
    i.pipeline_state_id
FROM resumes r
LEFT JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id AND cps.is_active = true
LEFT JOIN interview_sessions i ON r.id = i.resume_id
WHERE r.id = '912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5'
ORDER BY i.created_at DESC
LIMIT 1;