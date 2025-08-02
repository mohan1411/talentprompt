-- Fix interviews that are completed but missing overall_rating and recommendation
-- This calculates ratings from the interview questions

-- First, check which interviews need fixing
SELECT 
    i.id,
    r.first_name || ' ' || r.last_name as candidate_name,
    i.status,
    i.overall_rating,
    i.recommendation,
    COUNT(iq.id) as total_questions,
    COUNT(CASE WHEN iq.response_rating IS NOT NULL THEN 1 END) as rated_questions,
    AVG(iq.response_rating) as avg_question_rating
FROM interview_sessions i
JOIN resumes r ON i.resume_id = r.id
LEFT JOIN interview_questions iq ON i.id = iq.session_id
WHERE i.status = 'completed'
AND (i.overall_rating IS NULL OR i.recommendation IS NULL)
GROUP BY i.id, r.first_name, r.last_name, i.status, i.overall_rating, i.recommendation;

-- Update interviews with calculated ratings
UPDATE interview_sessions i
SET 
    overall_rating = subq.avg_rating,
    recommendation = CASE 
        WHEN subq.avg_rating >= 4 THEN 'hire'
        WHEN subq.avg_rating < 2 THEN 'no_hire'
        ELSE 'maybe'
    END,
    updated_at = NOW()
FROM (
    SELECT 
        i.id,
        ROUND(AVG(iq.response_rating)::numeric, 1) as avg_rating
    FROM interview_sessions i
    JOIN interview_questions iq ON i.id = iq.session_id
    WHERE i.status = 'completed'
    AND (i.overall_rating IS NULL OR i.recommendation IS NULL)
    AND iq.response_rating IS NOT NULL
    GROUP BY i.id
    HAVING COUNT(iq.response_rating) > 0
) subq
WHERE i.id = subq.id;

-- For interviews with no rated questions, set default values
UPDATE interview_sessions
SET 
    overall_rating = 3.0,
    recommendation = 'maybe',
    updated_at = NOW()
WHERE status = 'completed'
AND (overall_rating IS NULL OR recommendation IS NULL)
AND id NOT IN (
    SELECT DISTINCT i.id
    FROM interview_sessions i
    JOIN interview_questions iq ON i.id = iq.session_id
    WHERE iq.response_rating IS NOT NULL
);

-- Now fix pipeline stages for completed interviews
-- This will move candidates to appropriate stages based on their ratings
UPDATE candidate_pipeline_states cps
SET 
    current_stage_id = CASE 
        WHEN i.recommendation = 'hire' OR i.overall_rating >= 4 THEN 'offer'
        WHEN i.recommendation = 'no_hire' OR i.overall_rating < 2 THEN 'rejected'
        ELSE cps.current_stage_id  -- Keep current stage for 'maybe'
    END,
    entered_stage_at = NOW(),
    updated_at = NOW()
FROM interview_sessions i
WHERE cps.id = i.pipeline_state_id
AND i.status = 'completed'
AND i.overall_rating IS NOT NULL
AND i.recommendation IS NOT NULL
AND cps.current_stage_id = 'interview'
AND (
    (i.recommendation = 'hire' OR i.overall_rating >= 4) OR
    (i.recommendation = 'no_hire' OR i.overall_rating < 2)
);

-- Verify the fixes
SELECT 
    r.first_name || ' ' || r.last_name as candidate_name,
    i.status as interview_status,
    i.overall_rating,
    i.recommendation,
    cps.current_stage_id as pipeline_stage,
    CASE 
        WHEN cps.current_stage_id = 'offer' AND (i.overall_rating >= 4 OR i.recommendation = 'hire') THEN 'CORRECT'
        WHEN cps.current_stage_id = 'rejected' AND (i.overall_rating < 2 OR i.recommendation = 'no_hire') THEN 'CORRECT'
        WHEN cps.current_stage_id = 'interview' AND i.recommendation = 'maybe' THEN 'CORRECT'
        ELSE 'CHECK'
    END as status
FROM interview_sessions i
JOIN resumes r ON i.resume_id = r.id
LEFT JOIN candidate_pipeline_states cps ON i.pipeline_state_id = cps.id
WHERE i.status = 'completed'
ORDER BY i.updated_at DESC;