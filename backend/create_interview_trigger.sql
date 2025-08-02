-- Create a trigger to automatically move candidates to Interview stage when interview is scheduled
CREATE OR REPLACE FUNCTION move_candidate_to_interview_on_schedule()
RETURNS TRIGGER AS $$
BEGIN
    -- Only process if pipeline_state_id is set
    IF NEW.pipeline_state_id IS NOT NULL THEN
        -- Update the candidate's pipeline stage to 'interview'
        UPDATE candidate_pipeline_states
        SET 
            current_stage_id = 'interview',
            entered_stage_at = NOW(),
            updated_at = NOW()
        WHERE id = NEW.pipeline_state_id
        AND current_stage_id != 'interview'
        AND is_active = true;
        
        -- Log the activity if the update happened
        IF FOUND THEN
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
                cps.candidate_id,
                NEW.pipeline_state_id,
                NEW.interviewer_id,
                'stage_changed',
                'screening',
                'interview',
                '{"reason": "Interview scheduled - automatically moved to Interview stage via trigger"}',
                NOW()
            FROM candidate_pipeline_states cps
            WHERE cps.id = NEW.pipeline_state_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
DROP TRIGGER IF EXISTS interview_scheduled_move_to_interview ON interview_sessions;
CREATE TRIGGER interview_scheduled_move_to_interview
    AFTER INSERT ON interview_sessions
    FOR EACH ROW
    EXECUTE FUNCTION move_candidate_to_interview_on_schedule();

-- Similarly, create a trigger for interview completion
CREATE OR REPLACE FUNCTION move_candidate_on_interview_complete()
RETURNS TRIGGER AS $$
BEGIN
    -- Only process if status changed to COMPLETED and pipeline_state_id exists
    IF NEW.status = 'COMPLETED' AND OLD.status != 'COMPLETED' AND NEW.pipeline_state_id IS NOT NULL THEN
        -- Move based on recommendation and rating
        IF (NEW.recommendation = 'hire' OR NEW.overall_rating >= 4) THEN
            -- Move to offer stage
            UPDATE candidate_pipeline_states
            SET 
                current_stage_id = 'offer',
                entered_stage_at = NOW(),
                updated_at = NOW()
            WHERE id = NEW.pipeline_state_id
            AND current_stage_id = 'interview'
            AND is_active = true;
            
            IF FOUND THEN
                INSERT INTO pipeline_activities (
                    id, candidate_id, pipeline_state_id, user_id,
                    activity_type, from_stage_id, to_stage_id, details, created_at
                )
                SELECT 
                    gen_random_uuid(), cps.candidate_id, NEW.pipeline_state_id, NEW.interviewer_id,
                    'stage_changed', 'interview', 'offer',
                    json_build_object('reason', 'Interview completed with hire recommendation', 
                                    'rating', NEW.overall_rating, 
                                    'recommendation', NEW.recommendation),
                    NOW()
                FROM candidate_pipeline_states cps
                WHERE cps.id = NEW.pipeline_state_id;
            END IF;
        ELSIF (NEW.recommendation = 'no_hire' OR NEW.overall_rating < 2) THEN
            -- Move to rejected stage
            UPDATE candidate_pipeline_states
            SET 
                current_stage_id = 'rejected',
                entered_stage_at = NOW(),
                updated_at = NOW()
            WHERE id = NEW.pipeline_state_id
            AND is_active = true;
            
            IF FOUND THEN
                INSERT INTO pipeline_activities (
                    id, candidate_id, pipeline_state_id, user_id,
                    activity_type, from_stage_id, to_stage_id, details, created_at
                )
                SELECT 
                    gen_random_uuid(), cps.candidate_id, NEW.pipeline_state_id, NEW.interviewer_id,
                    'stage_changed', cps.current_stage_id, 'rejected',
                    json_build_object('reason', 'Interview completed with no-hire recommendation', 
                                    'rating', NEW.overall_rating, 
                                    'recommendation', NEW.recommendation),
                    NOW()
                FROM candidate_pipeline_states cps
                WHERE cps.id = NEW.pipeline_state_id;
            END IF;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger for interview completion
DROP TRIGGER IF EXISTS interview_completed_move_stage ON interview_sessions;
CREATE TRIGGER interview_completed_move_stage
    AFTER UPDATE ON interview_sessions
    FOR EACH ROW
    EXECUTE FUNCTION move_candidate_on_interview_complete();

-- Test the trigger by checking if it exists
SELECT 
    tgname as trigger_name,
    tgrelid::regclass as table_name,
    proname as function_name
FROM pg_trigger t
JOIN pg_proc p ON t.tgfoid = p.oid
WHERE tgrelid::regclass::text = 'interview_sessions';