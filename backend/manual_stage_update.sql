-- Simple manual update for Michelle Garcia and any future candidates

-- 1. Move Michelle to Interview stage (simple update)
UPDATE candidate_pipeline_states
SET 
    current_stage_id = 'interview',
    entered_stage_at = NOW(),
    updated_at = NOW()
WHERE candidate_id = (
    SELECT id FROM resumes 
    WHERE LOWER(first_name) = 'michelle' 
    AND LOWER(last_name) = 'garcia'
    ORDER BY created_at DESC
    LIMIT 1
)
AND is_active = true
AND current_stage_id != 'interview';

-- 2. Create a simple function to move any candidate to interview stage
CREATE OR REPLACE FUNCTION move_to_interview_stage(p_candidate_id UUID)
RETURNS TEXT AS $$
DECLARE
    rows_updated INT;
BEGIN
    UPDATE candidate_pipeline_states
    SET 
        current_stage_id = 'interview',
        entered_stage_at = NOW(),
        updated_at = NOW()
    WHERE candidate_id = p_candidate_id
    AND is_active = true
    AND current_stage_id != 'interview';
    
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    
    IF rows_updated > 0 THEN
        RETURN 'Moved to interview stage';
    ELSE
        RETURN 'No update needed or candidate not found';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 3. Check all recent interviews that should have triggered movement
SELECT 
    r.first_name || ' ' || r.last_name as candidate_name,
    r.id as resume_id,
    cps.current_stage_id,
    i.created_at as interview_scheduled_at,
    i.pipeline_state_id,
    CASE 
        WHEN cps.current_stage_id = 'screening' THEN 'Needs to move to interview'
        WHEN cps.current_stage_id = 'interview' THEN 'Already in interview'
        ELSE 'In stage: ' || cps.current_stage_id
    END as status
FROM interview_sessions i
JOIN resumes r ON i.resume_id = r.id
LEFT JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id AND cps.is_active = true
WHERE i.created_at > NOW() - INTERVAL '24 hours'
AND i.pipeline_state_id IS NOT NULL
ORDER BY i.created_at DESC;

-- 4. Fix all candidates who have interviews but are still in screening
UPDATE candidate_pipeline_states cps
SET 
    current_stage_id = 'interview',
    entered_stage_at = NOW(),
    updated_at = NOW()
FROM interview_sessions i
WHERE cps.candidate_id = i.resume_id
AND cps.is_active = true
AND cps.current_stage_id = 'screening'
AND i.pipeline_state_id IS NOT NULL
AND i.created_at > NOW() - INTERVAL '24 hours';

-- 5. Verify all updates
SELECT 
    r.first_name || ' ' || r.last_name as candidate_name,
    cps.current_stage_id as current_stage,
    COUNT(i.id) as interview_count
FROM candidate_pipeline_states cps
JOIN resumes r ON cps.candidate_id = r.id
LEFT JOIN interview_sessions i ON r.id = i.resume_id
WHERE cps.is_active = true
GROUP BY r.id, r.first_name, r.last_name, cps.current_stage_id
HAVING COUNT(i.id) > 0
ORDER BY r.first_name;