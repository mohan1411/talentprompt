-- Check current pipeline stages
SELECT id, name, jsonb_array_length(stages) as stage_count 
FROM pipelines 
WHERE is_default = true;

-- Add rejected and withdrawn stages if they don't exist
UPDATE pipelines
SET stages = stages || '[
    {"id": "rejected", "name": "Rejected", "order": 6, "color": "#ef4444", "type": "final", "actions": []},
    {"id": "withdrawn", "name": "Withdrawn", "order": 7, "color": "#6b7280", "type": "final", "actions": []}
]'::jsonb,
updated_at = NOW()
WHERE is_default = true
  AND NOT (stages @> '[{"id": "rejected"}]'::jsonb);

-- Verify the update
SELECT id, name, jsonb_array_length(stages) as stage_count 
FROM pipelines 
WHERE is_default = true;

-- Show all stages
SELECT jsonb_array_elements(stages) AS stage
FROM pipelines
WHERE is_default = true;

-- Check for candidates with low ratings not in rejected stage
SELECT 
    r.id, r.first_name, r.last_name,
    i.overall_rating, i.recommendation,
    cps.current_stage_id,
    cps.id as pipeline_state_id
FROM interview_sessions i
JOIN resumes r ON i.resume_id = r.id
LEFT JOIN candidate_pipeline_state cps ON i.pipeline_state_id = cps.id
WHERE i.overall_rating <= 2.0
  AND i.status = 'completed'
  AND (cps.current_stage_id != 'rejected' OR cps.current_stage_id IS NULL);

-- Move candidates with rating <= 2.0 to rejected stage
UPDATE candidate_pipeline_state cps
SET current_stage_id = 'rejected',
    entered_stage_at = NOW(),
    updated_at = NOW()
FROM interview_sessions i
WHERE cps.id = i.pipeline_state_id
  AND i.overall_rating <= 2.0
  AND i.status = 'completed'
  AND cps.current_stage_id != 'rejected';

-- Show updated candidates
SELECT 
    r.first_name || ' ' || r.last_name as candidate_name,
    cps.current_stage_id,
    i.overall_rating
FROM candidate_pipeline_state cps
JOIN resumes r ON r.id = cps.candidate_id
LEFT JOIN interview_sessions i ON i.pipeline_state_id = cps.id
ORDER BY cps.current_stage_id, r.first_name;