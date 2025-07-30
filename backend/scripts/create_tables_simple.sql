-- Simple SQL to create candidate submission tables
-- Run this directly in Railway Query tab or any PostgreSQL client

-- First, create invitation_campaigns without foreign key
CREATE TABLE IF NOT EXISTS invitation_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_type VARCHAR(50),
    source_data JSONB,
    is_public BOOLEAN DEFAULT FALSE,
    public_slug VARCHAR(100),
    email_template TEXT,
    expires_in_days INTEGER DEFAULT 7,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Then create candidate_submissions
CREATE TABLE IF NOT EXISTS candidate_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(255) UNIQUE NOT NULL,
    submission_type VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    recruiter_id UUID NOT NULL,
    campaign_id UUID,
    resume_id UUID,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    linkedin_url VARCHAR(255),
    availability VARCHAR(50),
    salary_expectations JSONB,
    location_preferences JSONB,
    resume_text TEXT,
    parsed_data JSONB,
    email_sent_at TIMESTAMP,
    email_opened_at TIMESTAMP,
    link_clicked_at TIMESTAMP,
    submitted_at TIMESTAMP,
    processed_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign keys if tables exist
DO $$ 
BEGIN
    -- Add foreign key to users table if it exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE invitation_campaigns 
        ADD CONSTRAINT fk_invitation_campaigns_recruiter 
        FOREIGN KEY (recruiter_id) REFERENCES users(id)
        ON DELETE CASCADE;
        
        ALTER TABLE candidate_submissions 
        ADD CONSTRAINT fk_candidate_submissions_recruiter 
        FOREIGN KEY (recruiter_id) REFERENCES users(id)
        ON DELETE CASCADE;
    END IF;
    
    -- Add foreign key to resumes table if it exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'resumes') THEN
        ALTER TABLE candidate_submissions 
        ADD CONSTRAINT fk_candidate_submissions_resume 
        FOREIGN KEY (resume_id) REFERENCES resumes(id)
        ON DELETE SET NULL;
    END IF;
    
    -- Add foreign key between tables
    ALTER TABLE candidate_submissions 
    ADD CONSTRAINT fk_candidate_submissions_campaign 
    FOREIGN KEY (campaign_id) REFERENCES invitation_campaigns(id)
    ON DELETE SET NULL;
EXCEPTION
    WHEN others THEN
        -- Ignore constraint errors
        NULL;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_candidate_submissions_token ON candidate_submissions(token);
CREATE INDEX IF NOT EXISTS ix_candidate_submissions_recruiter_id ON candidate_submissions(recruiter_id);
CREATE INDEX IF NOT EXISTS ix_candidate_submissions_email ON candidate_submissions(email);
CREATE INDEX IF NOT EXISTS ix_candidate_submissions_status ON candidate_submissions(status);
CREATE INDEX IF NOT EXISTS ix_invitation_campaigns_recruiter_id ON invitation_campaigns(recruiter_id);
CREATE INDEX IF NOT EXISTS ix_invitation_campaigns_public_slug ON invitation_campaigns(public_slug);

-- Verify tables were created
SELECT 'Tables created:' as message;
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN ('candidate_submissions', 'invitation_campaigns')
ORDER BY table_name;