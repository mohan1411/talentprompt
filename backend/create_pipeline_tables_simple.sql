-- Create Pipeline Management Tables for Promtitude
-- This version works without the update_updated_at_column function

-- Create pipeline stages enum
DO $$ BEGIN
    CREATE TYPE pipeline_stage_type AS ENUM (
        'sourced',
        'screening',
        'phone_interview',
        'technical_interview',
        'onsite_interview',
        'reference_check',
        'offer',
        'hired',
        'rejected',
        'withdrawn'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create activity types enum
DO $$ BEGIN
    CREATE TYPE pipeline_activity_type AS ENUM (
        'stage_changed',
        'assigned',
        'unassigned',
        'note_added',
        'email_sent',
        'email_received',
        'interview_scheduled',
        'interview_completed',
        'evaluation_submitted',
        'offer_extended',
        'offer_accepted',
        'offer_rejected',
        'candidate_withdrawn',
        'rejected'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Main pipelines table - defines workflow templates
CREATE TABLE IF NOT EXISTS pipelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    stages JSONB NOT NULL DEFAULT '[]',
    team_id UUID,
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_default_pipeline_per_team UNIQUE NULLS NOT DISTINCT (team_id, is_default)
);

-- Track each candidate's position in a pipeline
CREATE TABLE IF NOT EXISTS candidate_pipeline_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    pipeline_id UUID NOT NULL REFERENCES pipelines(id),
    current_stage_id VARCHAR(50) NOT NULL,
    current_stage_type pipeline_stage_type,
    assigned_to UUID REFERENCES users(id),
    assigned_at TIMESTAMP,
    entered_stage_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_in_stage_seconds INTEGER DEFAULT 0,
    rejection_reason TEXT,
    rejection_details JSONB,
    withdrawal_reason TEXT,
    is_active BOOLEAN DEFAULT true,
    tags JSONB DEFAULT '[]',
    custom_fields JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_active_candidate_pipeline UNIQUE (candidate_id, pipeline_id, is_active)
);

-- Activity log for all pipeline actions
CREATE TABLE IF NOT EXISTS pipeline_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    pipeline_state_id UUID REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    activity_type pipeline_activity_type NOT NULL,
    from_stage_id VARCHAR(50),
    to_stage_id VARCHAR(50),
    details JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comments and notes on candidates
CREATE TABLE IF NOT EXISTS candidate_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    pipeline_state_id UUID REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    is_private BOOLEAN DEFAULT false,
    mentioned_users UUID[] DEFAULT '{}',
    attachments JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interview feedback and evaluations
CREATE TABLE IF NOT EXISTS candidate_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    pipeline_state_id UUID REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
    evaluator_id UUID NOT NULL REFERENCES users(id),
    interview_id UUID REFERENCES interview_sessions(id),
    stage_id VARCHAR(50) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    strengths TEXT,
    concerns TEXT,
    technical_assessment JSONB,
    cultural_fit_assessment JSONB,
    recommendation VARCHAR(50) CHECK (recommendation IN ('strong_yes', 'yes', 'neutral', 'no', 'strong_no')),
    would_work_with BOOLEAN,
    evaluation_form JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_evaluation_per_stage UNIQUE (candidate_id, evaluator_id, stage_id)
);

-- Email thread tracking
CREATE TABLE IF NOT EXISTS candidate_communications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    pipeline_state_id UUID REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    direction VARCHAR(10) CHECK (direction IN ('inbound', 'outbound')),
    channel VARCHAR(50) DEFAULT 'email',
    subject VARCHAR(500),
    content TEXT,
    thread_id VARCHAR(255),
    message_id VARCHAR(255),
    in_reply_to VARCHAR(255),
    attachments JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    replied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pipeline automation rules
CREATE TABLE IF NOT EXISTS pipeline_automations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_type VARCHAR(50) NOT NULL,
    trigger_config JSONB NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    action_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Team assignments and permissions
CREATE TABLE IF NOT EXISTS pipeline_team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(50) DEFAULT 'member',
    stage_permissions JSONB DEFAULT '{}',
    can_move_candidates BOOLEAN DEFAULT true,
    can_evaluate BOOLEAN DEFAULT true,
    can_communicate BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_pipeline_member UNIQUE (pipeline_id, user_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_candidate_pipeline_states_candidate ON candidate_pipeline_states(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_pipeline_states_pipeline ON candidate_pipeline_states(pipeline_id);
CREATE INDEX IF NOT EXISTS idx_candidate_pipeline_states_assigned ON candidate_pipeline_states(assigned_to);
CREATE INDEX IF NOT EXISTS idx_candidate_pipeline_states_stage ON candidate_pipeline_states(current_stage_id);
CREATE INDEX IF NOT EXISTS idx_candidate_pipeline_states_active ON candidate_pipeline_states(is_active);

CREATE INDEX IF NOT EXISTS idx_pipeline_activities_candidate ON pipeline_activities(candidate_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_activities_user ON pipeline_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_activities_type ON pipeline_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_pipeline_activities_created ON pipeline_activities(created_at);

CREATE INDEX IF NOT EXISTS idx_candidate_notes_candidate ON candidate_notes(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_notes_user ON candidate_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_candidate_notes_created ON candidate_notes(created_at);

CREATE INDEX IF NOT EXISTS idx_candidate_evaluations_candidate ON candidate_evaluations(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_evaluations_evaluator ON candidate_evaluations(evaluator_id);
CREATE INDEX IF NOT EXISTS idx_candidate_evaluations_stage ON candidate_evaluations(stage_id);

CREATE INDEX IF NOT EXISTS idx_candidate_communications_candidate ON candidate_communications(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_communications_thread ON candidate_communications(thread_id);
CREATE INDEX IF NOT EXISTS idx_candidate_communications_sent ON candidate_communications(sent_at);

-- Insert default pipeline template
INSERT INTO pipelines (
    name,
    description,
    stages,
    is_default,
    created_by
) VALUES (
    'Default Hiring Pipeline',
    'Standard hiring workflow for most positions',
    '[
        {"id": "sourced", "name": "Sourced", "order": 1, "color": "#94a3b8", "type": "sourced"},
        {"id": "screening", "name": "Screening", "order": 2, "color": "#60a5fa", "type": "screening"},
        {"id": "phone", "name": "Phone Interview", "order": 3, "color": "#a78bfa", "type": "phone_interview"},
        {"id": "technical", "name": "Technical Interview", "order": 4, "color": "#c084fc", "type": "technical_interview"},
        {"id": "onsite", "name": "Onsite Interview", "order": 5, "color": "#e879f9", "type": "onsite_interview"},
        {"id": "offer", "name": "Offer", "order": 6, "color": "#34d399", "type": "offer"},
        {"id": "hired", "name": "Hired", "order": 7, "color": "#10b981", "type": "hired"}
    ]'::jsonb,
    true,
    (SELECT id FROM users WHERE is_superuser = true LIMIT 1)
) ON CONFLICT DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Pipeline tables created successfully!';
END $$;