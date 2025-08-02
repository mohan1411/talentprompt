-- Comprehensive SQL script to fix all pipeline stage issues
-- Run each section separately in pgAdmin

-- ============================================
-- 1. CHECK CURRENT PIPELINE ISSUES
-- ============================================
-- Find candidates with completed interviews but wrong pipeline stages
SELECT 
    r.first_name || ' ' || r.last_name as candidate_name,
    r.id as resume_id,
    cps.id as pipeline_state_id,
    cps.current_stage_id as current_stage,
    i.id as interview_id,
    i.status as interview_status,
    i.overall_rating,
    i.recommendation,
    i.created_at as interview_date,
    CASE 
        WHEN i.overall_rating >= 4 OR i.recommendation = 'hire' THEN 'Should be in OFFER'
        WHEN i.overall_rating < 2 OR i.recommendation = 'no_hire' THEN 'Should be in REJECTED'
        ELSE 'Should be in INTERVIEW or current stage'
    END as expected_stage
FROM resumes r
JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id
JOIN interview_sessions i ON r.id = i.resume_id AND i.pipeline_state_id = cps.id
WHERE cps.is_active = true
AND i.status = 'completed'
AND (
    -- Completed with high rating but not in offer
    (i.overall_rating >= 4 OR i.recommendation = 'hire') AND cps.current_stage_id != 'offer'
    OR
    -- Completed with low rating but not rejected
    (i.overall_rating < 2 OR i.recommendation = 'no_hire') AND cps.current_stage_id != 'rejected'
)
ORDER BY i.created_at DESC;

-- ============================================
-- 2. FIX CANDIDATES WHO SHOULD BE IN OFFER
-- ============================================
-- Move candidates with positive interview outcomes to offer stage
WITH candidates_to_offer AS (
    SELECT 
        cps.id as pipeline_state_id,
        cps.candidate_id,
        cps.current_stage_id,
        i.id as interview_id,
        i.interviewer_id,
        i.overall_rating,
        i.recommendation
    FROM candidate_pipeline_states cps
    JOIN interview_sessions i ON cps.candidate_id = i.resume_id AND i.pipeline_state_id = cps.id
    WHERE cps.is_active = true
    AND i.status = 'completed'
    AND (i.overall_rating >= 4 OR i.recommendation = 'hire')
    AND cps.current_stage_id NOT IN ('offer', 'hired')
)
UPDATE candidate_pipeline_states
SET 
    current_stage_id = 'offer',
    entered_stage_at = NOW(),
    updated_at = NOW(),
    time_in_stage_seconds = EXTRACT(EPOCH FROM (NOW() - entered_stage_at))
FROM candidates_to_offer cto
WHERE candidate_pipeline_states.id = cto.pipeline_state_id;

-- Log activities for offer moves
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
    cto.candidate_id,
    cto.pipeline_state_id,
    cto.interviewer_id,
    'stage_changed',
    cto.current_stage_id,
    'offer',
    jsonb_build_object(
        'reason', 'Batch fix - Interview completed with positive outcome',
        'interview_id', cto.interview_id::text,
        'interview_rating', cto.overall_rating,
        'interview_recommendation', cto.recommendation
    ),
    NOW()
FROM (
    SELECT DISTINCT ON (cps.id)
        cps.id as pipeline_state_id,
        cps.candidate_id,
        'interview' as current_stage_id, -- Assume they were in interview
        i.id as interview_id,
        i.interviewer_id,
        i.overall_rating,
        i.recommendation
    FROM candidate_pipeline_states cps
    JOIN interview_sessions i ON cps.candidate_id = i.resume_id AND i.pipeline_state_id = cps.id
    WHERE cps.is_active = true
    AND i.status = 'completed'
    AND (i.overall_rating >= 4 OR i.recommendation = 'hire')
    AND cps.current_stage_id = 'offer' -- Only log if we actually moved to offer
    ORDER BY cps.id, i.created_at DESC
) cto;

-- ============================================
-- 3. FIX CANDIDATES WHO SHOULD BE REJECTED
-- ============================================
-- Move candidates with negative interview outcomes to rejected stage
WITH candidates_to_reject AS (
    SELECT 
        cps.id as pipeline_state_id,
        cps.candidate_id,
        cps.current_stage_id,
        i.id as interview_id,
        i.interviewer_id,
        i.overall_rating,
        i.recommendation
    FROM candidate_pipeline_states cps
    JOIN interview_sessions i ON cps.candidate_id = i.resume_id AND i.pipeline_state_id = cps.id
    WHERE cps.is_active = true
    AND i.status = 'completed'
    AND (i.overall_rating < 2 OR i.recommendation = 'no_hire')
    AND cps.current_stage_id NOT IN ('rejected', 'withdrawn')
)
UPDATE candidate_pipeline_states
SET 
    current_stage_id = 'rejected',
    entered_stage_at = NOW(),
    updated_at = NOW(),
    time_in_stage_seconds = EXTRACT(EPOCH FROM (NOW() - entered_stage_at)),
    rejection_reason = 'Interview completed with negative outcome'
FROM candidates_to_reject ctr
WHERE candidate_pipeline_states.id = ctr.pipeline_state_id;

-- Log activities for rejection moves
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
    ctr.candidate_id,
    ctr.pipeline_state_id,
    ctr.interviewer_id,
    'stage_changed',
    ctr.current_stage_id,
    'rejected',
    jsonb_build_object(
        'reason', 'Batch fix - Interview completed with negative outcome',
        'interview_id', ctr.interview_id::text,
        'interview_rating', ctr.overall_rating,
        'interview_recommendation', ctr.recommendation
    ),
    NOW()
FROM (
    SELECT DISTINCT ON (cps.id)
        cps.id as pipeline_state_id,
        cps.candidate_id,
        'interview' as current_stage_id, -- Assume they were in interview
        i.id as interview_id,
        i.interviewer_id,
        i.overall_rating,
        i.recommendation
    FROM candidate_pipeline_states cps
    JOIN interview_sessions i ON cps.candidate_id = i.resume_id AND i.pipeline_state_id = cps.id
    WHERE cps.is_active = true
    AND i.status = 'completed'
    AND (i.overall_rating < 2 OR i.recommendation = 'no_hire')
    AND cps.current_stage_id = 'rejected' -- Only log if we actually moved to rejected
    ORDER BY cps.id, i.created_at DESC
) ctr;

-- ============================================
-- 4. VERIFY FIXES
-- ============================================
-- Check if all candidates are now in correct stages
SELECT 
    r.first_name || ' ' || r.last_name as candidate_name,
    cps.current_stage_id as current_stage,
    i.overall_rating,
    i.recommendation,
    i.status as interview_status,
    CASE 
        WHEN cps.current_stage_id = 'offer' AND (i.overall_rating >= 4 OR i.recommendation = 'hire') THEN 'CORRECT'
        WHEN cps.current_stage_id = 'rejected' AND (i.overall_rating < 2 OR i.recommendation = 'no_hire') THEN 'CORRECT'
        WHEN cps.current_stage_id = 'interview' AND i.status != 'completed' THEN 'CORRECT'
        ELSE 'STILL NEEDS FIX'
    END as status
FROM resumes r
JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id
JOIN interview_sessions i ON r.id = i.resume_id AND i.pipeline_state_id = cps.id
WHERE cps.is_active = true
AND i.pipeline_state_id IS NOT NULL
ORDER BY status DESC, i.created_at DESC;