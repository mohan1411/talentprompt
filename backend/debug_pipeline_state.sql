-- Debug query to check Brian Williams' pipeline state

-- First, find Brian Williams' resume ID
SELECT id, first_name, last_name 
FROM resumes 
WHERE LOWER(first_name) = 'brian' AND LOWER(last_name) = 'williams';

-- Check if candidate has any pipeline states
SELECT 
    cps.*,
    r.first_name,
    r.last_name,
    p.name as pipeline_name
FROM candidate_pipeline_states cps
JOIN resumes r ON cps.candidate_id = r.id
JOIN pipelines p ON cps.pipeline_id = p.id
WHERE LOWER(r.first_name) = 'brian' AND LOWER(r.last_name) = 'williams';

-- Check all interview sessions for Brian Williams
SELECT 
    i.id,
    i.job_position,
    i.pipeline_state_id,
    i.status,
    i.recommendation,
    i.overall_rating,
    i.created_at,
    r.first_name,
    r.last_name
FROM interview_sessions i
JOIN resumes r ON i.resume_id = r.id
WHERE LOWER(r.first_name) = 'brian' AND LOWER(r.last_name) = 'williams'
ORDER BY i.created_at DESC;

-- Summary check for Brian Williams
WITH brian AS (
    SELECT id FROM resumes 
    WHERE LOWER(first_name) = 'brian' AND LOWER(last_name) = 'williams'
    LIMIT 1
)
SELECT 
    'Resume exists' as check_type,
    COUNT(*) as count
FROM resumes 
WHERE id IN (SELECT id FROM brian)
UNION ALL
SELECT 
    'Pipeline states' as check_type,
    COUNT(*) as count
FROM candidate_pipeline_states 
WHERE candidate_id IN (SELECT id FROM brian)
UNION ALL
SELECT 
    'Interviews' as check_type,
    COUNT(*) as count
FROM interview_sessions 
WHERE resume_id IN (SELECT id FROM brian)
UNION ALL
SELECT 
    'Interviews with pipeline link' as check_type,
    COUNT(*) as count
FROM interview_sessions 
WHERE resume_id IN (SELECT id FROM brian) 
AND pipeline_state_id IS NOT NULL;