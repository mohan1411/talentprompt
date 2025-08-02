-- Force update Brian to Offer stage
-- First, let's see the exact pipeline state ID

-- Get Brian's active pipeline state ID
SELECT id, current_stage_id 
FROM candidate_pipeline_states 
WHERE candidate_id = '912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5' 
AND is_active = true;

-- Copy the ID from above and use it here:
-- UPDATE candidate_pipeline_states
-- SET 
--     current_stage_id = 'offer',
--     entered_stage_at = NOW(),
--     updated_at = NOW()
-- WHERE id = '<paste_pipeline_state_id_here>';

-- Alternative: Update by candidate_id directly
BEGIN;

-- Update the pipeline state
UPDATE candidate_pipeline_states
SET 
    current_stage_id = 'offer',
    entered_stage_at = NOW(),
    updated_at = NOW()
WHERE candidate_id = '912b6e3c-34e4-4ed8-8836-2ccbdf2e10d5' 
AND is_active = true
RETURNING *;

-- If the above returns a row, commit the transaction
-- COMMIT;
-- If not, rollback
-- ROLLBACK;