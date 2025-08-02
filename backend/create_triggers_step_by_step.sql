-- Step 1: Create the function for moving to interview stage
CREATE OR REPLACE FUNCTION move_candidate_to_interview_on_schedule()
RETURNS TRIGGER AS $$
DECLARE
    old_stage_id TEXT;
    candidate_id_var UUID;
BEGIN
    -- Only process if pipeline_state_id is set
    IF NEW.pipeline_state_id IS NULL THEN
        RETURN NEW;
    END IF;
    
    -- Get the current stage and candidate_id
    SELECT current_stage_id, candidate_id 
    INTO old_stage_id, candidate_id_var
    FROM candidate_pipeline_states
    WHERE id = NEW.pipeline_state_id
    AND is_active = true;
    
    -- Only update if not already in interview stage
    IF old_stage_id IS NOT NULL AND old_stage_id != 'interview' THEN
        -- Update the candidate's pipeline stage to 'interview'
        UPDATE candidate_pipeline_states
        SET 
            current_stage_id = 'interview',
            entered_stage_at = NOW(),
            updated_at = NOW()
        WHERE id = NEW.pipeline_state_id;
        
        -- Log the activity
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
        VALUES (
            gen_random_uuid(),
            candidate_id_var,
            NEW.pipeline_state_id,
            NEW.interviewer_id,
            'stage_changed',
            old_stage_id,
            'interview',
            '{"reason": "Interview scheduled - automatically moved to Interview stage"}'::jsonb,
            NOW()
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 2: Create the trigger for interview scheduling
DROP TRIGGER IF EXISTS interview_scheduled_move_to_interview ON interview_sessions;
CREATE TRIGGER interview_scheduled_move_to_interview
    AFTER INSERT ON interview_sessions
    FOR EACH ROW
    EXECUTE FUNCTION move_candidate_to_interview_on_schedule();

-- Step 3: Test the function exists
SELECT proname, prosrc FROM pg_proc WHERE proname = 'move_candidate_to_interview_on_schedule';

-- Step 4: Test the trigger exists
SELECT tgname FROM pg_trigger WHERE tgname = 'interview_scheduled_move_to_interview';

-- Step 5: Move Michelle Garcia manually to test
UPDATE candidate_pipeline_states
SET 
    current_stage_id = 'interview',
    entered_stage_at = NOW(),
    updated_at = NOW()
WHERE candidate_id IN (
    SELECT id FROM resumes 
    WHERE LOWER(first_name) = 'michelle' 
    AND LOWER(last_name) = 'garcia'
    ORDER BY created_at DESC
    LIMIT 1
)
AND is_active = true
AND current_stage_id = 'screening';

-- Step 6: Verify Michelle's status
SELECT 
    r.first_name,
    r.last_name,
    cps.current_stage_id,
    cps.updated_at
FROM resumes r
JOIN candidate_pipeline_states cps ON r.id = cps.candidate_id
WHERE LOWER(r.first_name) = 'michelle' 
AND LOWER(r.last_name) = 'garcia'
AND cps.is_active = true;