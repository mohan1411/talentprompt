-- =====================================================
-- COMPLETE PRODUCTION MIGRATION SCRIPT
-- Creates all necessary tables for the entire application
-- =====================================================

-- 1. CREATE BASE TABLES FIRST

-- Create users table (if not exists)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create resumes table (if not exists)
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER,
    mime_type VARCHAR(100),
    parse_status VARCHAR(50) DEFAULT 'pending',
    parsed_data JSONB,
    vector_id VARCHAR(255),
    skills TEXT[],
    experience_years FLOAT,
    education_level VARCHAR(100),
    certifications TEXT[],
    languages TEXT[],
    location VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create candidates table (if not exists)
CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    current_title VARCHAR(255),
    current_company VARCHAR(255),
    years_of_experience FLOAT,
    skills TEXT[],
    education JSONB,
    experience JSONB,
    location VARCHAR(255),
    linkedin_url VARCHAR(500),
    github_url VARCHAR(500),
    portfolio_url VARCHAR(500),
    availability VARCHAR(100),
    salary_expectation VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on candidates email for uniqueness
CREATE UNIQUE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email) WHERE email IS NOT NULL;

-- Create jobs table (if not exists)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    requirements TEXT[],
    nice_to_have TEXT[],
    department VARCHAR(100),
    location VARCHAR(255),
    employment_type VARCHAR(50),
    salary_range VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create interview_sessions table (if not exists)
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    interviewer_id UUID REFERENCES users(id),
    scheduled_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER DEFAULT 60,
    meeting_link VARCHAR(500),
    status VARCHAR(50) DEFAULT 'scheduled',
    interview_type VARCHAR(50),
    interview_round INTEGER DEFAULT 1,
    notes TEXT,
    feedback JSONB,
    overall_rating NUMERIC(2,1),
    recommendation VARCHAR(50),
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    is_transcription_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create interview_questions table (if not exists)
CREATE TABLE IF NOT EXISTS interview_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    question_type VARCHAR(50),
    expected_answer TEXT,
    candidate_response TEXT,
    response_rating INTEGER CHECK (response_rating >= 1 AND response_rating <= 5),
    notes TEXT,
    asked_at TIMESTAMP WITH TIME ZONE,
    time_taken_seconds INTEGER,
    order_index INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create transcriptions table (if not exists)
CREATE TABLE IF NOT EXISTS transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    content TEXT,
    speaker VARCHAR(100),
    timestamp_start FLOAT,
    timestamp_end FLOAT,
    confidence FLOAT,
    is_final BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. CREATE PIPELINE FEATURE TABLES

-- Create enum types for pipeline
DO $$ BEGIN
    CREATE TYPE pipeline_stage_type AS ENUM ('applied', 'screening', 'interview', 'offer', 'hired', 'rejected', 'withdrawn');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE pipeline_activity_type AS ENUM ('moved', 'noted', 'assigned', 'tagged', 'contacted', 'evaluated');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create pipelines table
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

-- Create candidate_pipeline_states table
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

-- Create pipeline_activities table
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

-- Create candidate_notes table
CREATE TABLE IF NOT EXISTS candidate_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_state_id UUID NOT NULL REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
    note TEXT NOT NULL,
    is_private BOOLEAN DEFAULT false,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create candidate_evaluations table
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

-- Create candidate_communications table
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

-- Create pipeline_automations table
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

-- Create pipeline_team_members table
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
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_parse_status ON resumes(parse_status);
CREATE INDEX IF NOT EXISTS idx_candidates_resume_id ON candidates(resume_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_candidate ON interview_sessions(candidate_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_status ON interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_interview_questions_session ON interview_questions(session_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_states_candidate ON candidate_pipeline_states(candidate_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_states_pipeline ON candidate_pipeline_states(pipeline_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_states_stage ON candidate_pipeline_states(current_stage);
CREATE INDEX IF NOT EXISTS idx_pipeline_states_assigned ON candidate_pipeline_states(assigned_to);
CREATE INDEX IF NOT EXISTS idx_pipeline_activities_state ON pipeline_activities(pipeline_state_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_activities_type ON pipeline_activities(activity_type);

-- 4. ADD PIPELINE SUPPORT TO INTERVIEWS
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS pipeline_state_id UUID REFERENCES candidate_pipeline_states(id);

-- 5. CREATE DEFAULT PIPELINE
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

-- 7. VERIFY INSTALLATION
SELECT 
    'Tables Created' as check_type,
    COUNT(*) as count
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'candidates', 'resumes', 'pipelines', 'candidate_pipeline_states');

SELECT 
    'Default Pipeline' as check_type,
    COUNT(*) as count
FROM pipelines 
WHERE is_default = true;

-- =====================================================
-- Migration Complete!
-- =====================================================