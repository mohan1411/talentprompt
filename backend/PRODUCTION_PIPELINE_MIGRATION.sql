-- =====================================================
-- PRODUCTION PIPELINE MIGRATION SCRIPT
-- Run this on your production database to enable Pipeline & Workflow Management
-- =====================================================

-- 1. CREATE ENUM TYPES
CREATE TYPE pipeline_stage_type AS ENUM ('applied', 'screening', 'interview', 'offer', 'hired', 'rejected', 'withdrawn');
CREATE TYPE pipeline_activity_type AS ENUM ('moved', 'noted', 'assigned', 'tagged', 'contacted', 'evaluated');

-- 2. CREATE PIPELINE TABLES
CREATE TABLE IF NOT EXISTS pipelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    stages JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    CONSTRAINT only_one_default_pipeline UNIQUE (is_default) WHERE is_default = true
);

CREATE TABLE IF NOT EXISTS candidate_pipeline_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    current_stage VARCHAR(50) NOT NULL,
    stage_entered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_to UUID REFERENCES users(id),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(candidate_id, pipeline_id)
);

CREATE TABLE IF NOT EXISTS pipeline_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_state_id UUID NOT NULL REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
    activity_type pipeline_activity_type NOT NULL,
    from_stage VARCHAR(50),
    to_stage VARCHAR(50),
    performed_by UUID REFERENCES users(id),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidate_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_state_id UUID NOT NULL REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
    note TEXT NOT NULL,
    is_private BOOLEAN DEFAULT false,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidate_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_state_id UUID NOT NULL REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
    interview_session_id UUID REFERENCES interview_sessions(id),
    evaluator_id UUID REFERENCES users(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    strengths TEXT[],
    weaknesses TEXT[],
    recommendation VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidate_communications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_state_id UUID NOT NULL REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
    communication_type VARCHAR(50) NOT NULL,
    subject VARCHAR(255),
    content TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    sent_by UUID REFERENCES users(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_automations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    trigger_stage VARCHAR(50),
    trigger_condition JSONB,
    action_type VARCHAR(50) NOT NULL,
    action_config JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    permissions JSONB DEFAULT '{}',
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    added_by UUID REFERENCES users(id),
    UNIQUE(pipeline_id, user_id)
);

-- 3. CREATE INDEXES
CREATE INDEX idx_pipeline_states_candidate ON candidate_pipeline_states(candidate_id);
CREATE INDEX idx_pipeline_states_pipeline ON candidate_pipeline_states(pipeline_id);
CREATE INDEX idx_pipeline_states_stage ON candidate_pipeline_states(current_stage);
CREATE INDEX idx_pipeline_states_assigned ON candidate_pipeline_states(assigned_to);
CREATE INDEX idx_pipeline_activities_state ON pipeline_activities(pipeline_state_id);
CREATE INDEX idx_pipeline_activities_type ON pipeline_activities(activity_type);
CREATE INDEX idx_candidate_notes_state ON candidate_notes(pipeline_state_id);
CREATE INDEX idx_candidate_evaluations_state ON candidate_evaluations(pipeline_state_id);
CREATE INDEX idx_candidate_communications_state ON candidate_communications(pipeline_state_id);

-- 4. ADD PIPELINE SUPPORT TO INTERVIEWS
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS pipeline_state_id UUID REFERENCES candidate_pipeline_states(id);

-- 5. CREATE DEFAULT PIPELINE WITH ALL 7 STAGES
INSERT INTO pipelines (
    name, 
    description, 
    stages, 
    is_active, 
    is_default
)
VALUES (
    'Default Hiring Pipeline',
    'Standard recruitment workflow with all stages including terminal states',
    '[
        {
            "id": "applied",
            "name": "Applied",
            "description": "New applications",
            "color": "#6B7280",
            "order": 1,
            "is_terminal": false
        },
        {
            "id": "screening",
            "name": "Screening",
            "description": "Initial review and screening",
            "color": "#3B82F6",
            "order": 2,
            "is_terminal": false
        },
        {
            "id": "interview",
            "name": "Interview",
            "description": "Interview process",
            "color": "#8B5CF6",
            "order": 3,
            "is_terminal": false
        },
        {
            "id": "offer",
            "name": "Offer",
            "description": "Offer extended",
            "color": "#F59E0B",
            "order": 4,
            "is_terminal": false
        },
        {
            "id": "hired",
            "name": "Hired",
            "description": "Successfully hired",
            "color": "#10B981",
            "order": 5,
            "is_terminal": false
        },
        {
            "id": "rejected",
            "name": "Rejected",
            "description": "Not selected for position",
            "color": "#EF4444",
            "order": 6,
            "is_terminal": true
        },
        {
            "id": "withdrawn",
            "name": "Withdrawn",
            "description": "Candidate withdrew from process",
            "color": "#6B7280",
            "order": 7,
            "is_terminal": true
        }
    ]'::jsonb,
    true,
    true
) ON CONFLICT (is_default) WHERE is_default = true DO NOTHING;

-- 6. CREATE TRIGGER FOR AUTOMATIC STAGE TRANSITIONS
CREATE OR REPLACE FUNCTION update_pipeline_stage_on_interview()
RETURNS TRIGGER AS $$
DECLARE
    v_pipeline_state_id UUID;
BEGIN
    -- Only proceed if status is changing to 'scheduled'
    IF NEW.status = 'scheduled' AND (OLD.status IS NULL OR OLD.status != 'scheduled') THEN
        -- Get the pipeline_state_id
        v_pipeline_state_id := NEW.pipeline_state_id;
        
        IF v_pipeline_state_id IS NOT NULL THEN
            -- Update the candidate's stage to 'interview'
            UPDATE candidate_pipeline_states
            SET current_stage = 'interview',
                stage_entered_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = v_pipeline_state_id;
            
            -- Log the activity
            INSERT INTO pipeline_activities (
                pipeline_state_id,
                activity_type,
                from_stage,
                to_stage,
                details,
                created_at
            )
            SELECT 
                v_pipeline_state_id,
                'moved'::pipeline_activity_type,
                current_stage,
                'interview',
                jsonb_build_object(
                    'reason', 'Interview scheduled',
                    'automated', true,
                    'interview_id', NEW.id
                ),
                CURRENT_TIMESTAMP
            FROM candidate_pipeline_states
            WHERE id = v_pipeline_state_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS interview_scheduled_pipeline_update ON interview_sessions;

CREATE TRIGGER interview_scheduled_pipeline_update
AFTER INSERT OR UPDATE ON interview_sessions
FOR EACH ROW
EXECUTE FUNCTION update_pipeline_stage_on_interview();

-- 7. MIGRATE EXISTING DATA (if you have existing candidates/interviews)
-- Add all existing candidates to the default pipeline
INSERT INTO candidate_pipeline_states (
    candidate_id,
    pipeline_id,
    current_stage,
    stage_entered_at
)
SELECT 
    c.id,
    p.id,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM interview_sessions i 
            WHERE i.candidate_id = c.id 
            AND i.status = 'completed'
            AND i.overall_rating >= 4
        ) THEN 'offer'
        WHEN EXISTS (
            SELECT 1 FROM interview_sessions i 
            WHERE i.candidate_id = c.id 
            AND i.status = 'completed'
            AND i.overall_rating <= 2
        ) THEN 'rejected'
        WHEN EXISTS (
            SELECT 1 FROM interview_sessions i 
            WHERE i.candidate_id = c.id 
            AND i.status IN ('scheduled', 'in_progress', 'completed')
        ) THEN 'interview'
        ELSE 'applied'
    END as current_stage,
    CURRENT_TIMESTAMP
FROM candidates c
CROSS JOIN pipelines p
WHERE p.is_default = true
AND NOT EXISTS (
    SELECT 1 FROM candidate_pipeline_states cps
    WHERE cps.candidate_id = c.id
    AND cps.pipeline_id = p.id
)
ON CONFLICT (candidate_id, pipeline_id) DO NOTHING;

-- Link existing interviews to pipeline states
UPDATE interview_sessions i
SET pipeline_state_id = cps.id
FROM candidate_pipeline_states cps
JOIN pipelines p ON p.id = cps.pipeline_id
WHERE i.candidate_id = cps.candidate_id
AND p.is_default = true
AND i.pipeline_state_id IS NULL;

-- 8. VERIFY MIGRATION
DO $$
DECLARE
    v_tables_count INTEGER;
    v_pipeline_count INTEGER;
    v_candidates_in_pipeline INTEGER;
BEGIN
    -- Check tables exist
    SELECT COUNT(*) INTO v_tables_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('pipelines', 'candidate_pipeline_states', 'pipeline_activities');
    
    -- Check default pipeline exists
    SELECT COUNT(*) INTO v_pipeline_count
    FROM pipelines
    WHERE is_default = true;
    
    -- Check candidates are in pipeline
    SELECT COUNT(*) INTO v_candidates_in_pipeline
    FROM candidate_pipeline_states;
    
    RAISE NOTICE 'Migration Status:';
    RAISE NOTICE '  Tables created: %', v_tables_count;
    RAISE NOTICE '  Default pipeline: %', CASE WHEN v_pipeline_count > 0 THEN 'Yes' ELSE 'No' END;
    RAISE NOTICE '  Candidates in pipeline: %', v_candidates_in_pipeline;
END $$;

-- =====================================================
-- Migration Complete!
-- Your pipeline system is now ready for use
-- =====================================================