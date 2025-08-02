-- Debug Brian Williams pipeline issue
-- ID: 912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5

-- 1. Check if Brian has an active pipeline state
SELECT 
    cps.id as pipeline_state_id,
    cps.candidate_id,
    cps.pipeline_id,
    cps.current_stage_id,
    cps.is_active,
    cps.entered_stage_at,
    cps.updated_at,
    p.name as pipeline_name
FROM candidate_pipeline_states cps
JOIN pipelines p ON cps.pipeline_id = p.id
WHERE cps.candidate_id = '912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5';

-- 2. Check interview details
SELECT 
    id,
    resume_id,
    status,
    overall_rating,
    recommendation,
    pipeline_state_id,
    created_at,
    updated_at
FROM interview_sessions
WHERE resume_id = '912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5'
ORDER BY created_at DESC;

-- 3. Check pipeline activities
SELECT 
    id,
    activity_type,
    from_stage_id,
    to_stage_id,
    details,
    created_at
FROM pipeline_activities
WHERE candidate_id = '912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5'
ORDER BY created_at DESC
LIMIT 10;

-- 4. Check if the pipeline has an 'offer' stage
SELECT 
    p.id,
    p.name,
    p.stages
FROM pipelines p
JOIN candidate_pipeline_states cps ON p.id = cps.pipeline_id
WHERE cps.candidate_id = '912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5'
AND cps.is_active = true;