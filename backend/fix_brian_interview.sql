-- 1. First, find all Brian Williams entries
SELECT id, first_name, last_name, created_at 
FROM resumes 
WHERE LOWER(first_name) = 'brian' AND LOWER(last_name) = 'williams';

-- 2. Check the most recent Brian Williams' interview status
WITH latest_brian AS (
    SELECT id FROM resumes 
    WHERE LOWER(first_name) = 'brian' AND LOWER(last_name) = 'williams'
    ORDER BY created_at DESC
    LIMIT 1
)
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
    cps.id as pipeline_state_id,
    cps.current_stage_id as pipeline_stage
FROM interview_sessions i
JOIN resumes r ON i.resume_id = r.id
LEFT JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id AND cps.is_active = true
WHERE r.id IN (SELECT id FROM latest_brian)
ORDER BY i.created_at DESC;

-- 3. Update the most recent interview to completed with hire recommendation
WITH latest_brian AS (
    SELECT id FROM resumes 
    WHERE LOWER(first_name) = 'brian' AND LOWER(last_name) = 'williams'
    ORDER BY created_at DESC
    LIMIT 1
),
latest_interview AS (
    SELECT i.id 
    FROM interview_sessions i
    WHERE i.resume_id IN (SELECT id FROM latest_brian)
    AND i.status != 'COMPLETED'
    ORDER BY i.created_at DESC
    LIMIT 1
)
UPDATE interview_sessions 
SET 
    status = 'COMPLETED',
    overall_rating = 4.3,
    recommendation = 'hire',
    ended_at = NOW()
WHERE id IN (SELECT id FROM latest_interview);

-- 4. Move the most recent Brian to Offer stage
WITH latest_brian AS (
    SELECT id FROM resumes 
    WHERE LOWER(first_name) = 'brian' AND LOWER(last_name) = 'williams'
    ORDER BY created_at DESC
    LIMIT 1
)
UPDATE candidate_pipeline_states
SET 
    current_stage_id = 'offer',
    entered_stage_at = NOW(),
    updated_at = NOW()
WHERE candidate_id IN (SELECT id FROM latest_brian)
AND is_active = true;

-- 5. Verify the update
WITH latest_brian AS (
    SELECT id FROM resumes 
    WHERE LOWER(first_name) = 'brian' AND LOWER(last_name) = 'williams'
    ORDER BY created_at DESC
    LIMIT 1
)
SELECT 
    r.id,
    r.first_name,
    r.last_name,
    cps.current_stage_id,
    i.status as interview_status,
    i.overall_rating,
    i.recommendation
FROM resumes r
LEFT JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id AND cps.is_active = true
LEFT JOIN interview_sessions i ON r.id = i.resume_id
WHERE r.id IN (SELECT id FROM latest_brian)
ORDER BY i.created_at DESC
LIMIT 1;