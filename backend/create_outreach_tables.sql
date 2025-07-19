-- Create enum types if they don't exist
DO $$ BEGIN
    CREATE TYPE messagestyle AS ENUM ('casual', 'professional', 'technical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE messagestatus AS ENUM ('generated', 'sent', 'opened', 'responded', 'not_interested');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create outreach_messages table
CREATE TABLE IF NOT EXISTS outreach_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    resume_id UUID NOT NULL REFERENCES resumes(id),
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    style messagestyle NOT NULL,
    job_title VARCHAR(255),
    job_requirements JSON,
    company_name VARCHAR(255),
    status messagestatus DEFAULT 'generated',
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    responded_at TIMESTAMP,
    quality_score FLOAT,
    response_rate FLOAT,
    generation_prompt TEXT,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_outreach_messages_user_id ON outreach_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_outreach_messages_resume_id ON outreach_messages(resume_id);
CREATE INDEX IF NOT EXISTS idx_outreach_messages_status ON outreach_messages(status);
CREATE INDEX IF NOT EXISTS idx_outreach_messages_created_at ON outreach_messages(created_at);

-- Create outreach_templates table
CREATE TABLE IF NOT EXISTS outreach_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    subject_template VARCHAR(500),
    body_template TEXT NOT NULL,
    style messagestyle NOT NULL,
    industry VARCHAR(100),
    role_level VARCHAR(50),
    job_function VARCHAR(100),
    times_used INTEGER DEFAULT 0,
    avg_response_rate FLOAT,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for templates
CREATE INDEX IF NOT EXISTS idx_outreach_templates_user_id ON outreach_templates(user_id);
CREATE INDEX IF NOT EXISTS idx_outreach_templates_is_public ON outreach_templates(is_public);
CREATE INDEX IF NOT EXISTS idx_outreach_templates_style ON outreach_templates(style);

-- Update alembic version to mark migration as complete
DELETE FROM alembic_version WHERE version_num = 'add_outreach_tables';
INSERT INTO alembic_version (version_num) VALUES ('add_outreach_tables');