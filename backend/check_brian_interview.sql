-- Check Brian Williams' interview status
SELECT 
    i.id,
    i.job_position,
    i.status,
    i.overall_rating,
    i.recommendation,
    i.pipeline_state_id,
    i.created_at,
    i.updated_at,
    r.first_name,
    r.last_name,
    cps.current_stage_id as pipeline_stage
FROM interview_sessions i
JOIN resumes r ON i.resume_id = r.id
LEFT JOIN candidate_pipeline_states cps ON i.pipeline_state_id = cps.id
WHERE LOWER(r.first_name) = 'brian' AND LOWER(r.last_name) = 'williams'
ORDER BY i.created_at DESC;

-- If the interview is not marked as COMPLETED, update it manually
-- UPDATE interview_sessions 
-- SET 
--     status = 'COMPLETED',
--     overall_rating = 4.3,
--     recommendation = 'hire',
--     ended_at = NOW()
-- WHERE id = '<interview_id_from_above>';