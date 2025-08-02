-- Execute this as a single DO block
DO $$
BEGIN
    -- Drop existing trigger and function
    DROP TRIGGER IF EXISTS interview_scheduled_move_to_interview ON interview_sessions;
    DROP FUNCTION IF EXISTS move_candidate_to_interview_on_schedule();
    
    -- Create the function
    EXECUTE '
    CREATE OR REPLACE FUNCTION move_candidate_to_interview_on_schedule()
    RETURNS TRIGGER AS $func$
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
        IF old_stage_id IS NOT NULL AND old_stage_id != ''interview'' THEN
            -- Update the candidates pipeline stage to interview
            UPDATE candidate_pipeline_states
            SET 
                current_stage_id = ''interview'',
                entered_stage_at = NOW(),
                updated_at = NOW()
            WHERE id = NEW.pipeline_state_id;
            
            -- Log the activity
            INSERT INTO pipeline_activities (
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
                candidate_id_var,
                NEW.pipeline_state_id,
                NEW.interviewer_id,
                ''stage_changed'',
                old_stage_id,
                ''interview'',
                ''{"reason": "Interview scheduled - automatically moved to Interview stage"}''::jsonb,
                NOW()
            );
        END IF;
        
        RETURN NEW;
    END;
    $func$ LANGUAGE plpgsql;
    ';
    
    -- Create the trigger
    EXECUTE '
    CREATE TRIGGER interview_scheduled_move_to_interview
        AFTER INSERT ON interview_sessions
        FOR EACH ROW
        EXECUTE FUNCTION move_candidate_to_interview_on_schedule();
    ';
    
    RAISE NOTICE 'Trigger created successfully';
END $$;