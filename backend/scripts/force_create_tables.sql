-- FORCE CREATE TABLES - Run this ENTIRE script in pgAdmin

-- Drop existing tables if they exist (to start fresh)
DROP TABLE IF EXISTS candidate_submissions CASCADE;
DROP TABLE IF EXISTS invitation_campaigns CASCADE;

-- Create invitation_campaigns
CREATE TABLE invitation_campaigns (
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

-- Create candidate_submissions
CREATE TABLE candidate_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(255) UNIQUE NOT NULL,
    submission_type VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    recruiter_id UUID NOT NULL,
    campaign_id UUID REFERENCES invitation_campaigns(id),
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

-- Create indexes
CREATE INDEX ix_candidate_submissions_token ON candidate_submissions(token);
CREATE INDEX ix_candidate_submissions_recruiter_id ON candidate_submissions(recruiter_id);
CREATE INDEX ix_candidate_submissions_email ON candidate_submissions(email);
CREATE INDEX ix_candidate_submissions_status ON candidate_submissions(status);
CREATE INDEX ix_invitation_campaigns_recruiter_id ON invitation_campaigns(recruiter_id);
CREATE INDEX ix_invitation_campaigns_public_slug ON invitation_campaigns(public_slug);

-- Verify creation
SELECT 
    'TABLES CREATED SUCCESSFULLY!' as message,
    COUNT(*) as tables_created
FROM information_schema.tables 
WHERE table_name IN ('candidate_submissions', 'invitation_campaigns')
AND table_schema = 'public';

-- Show the tables
SELECT table_name, 'CREATED' as status
FROM information_schema.tables 
WHERE table_name IN ('candidate_submissions', 'invitation_campaigns')
AND table_schema = 'public'
ORDER BY table_name;