-- STEP 1: Check which database you're connected to
SELECT current_database(), current_user, current_schema();

-- STEP 2: Check if tables exist in ANY schema
SELECT schemaname, tablename 
FROM pg_tables 
WHERE tablename IN ('candidate_submissions', 'invitation_campaigns')
ORDER BY schemaname, tablename;

-- STEP 3: Check your search path
SHOW search_path;

-- STEP 4: List ALL tables in the public schema
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- STEP 5: Force create tables in public schema with explicit schema reference
BEGIN;

CREATE TABLE IF NOT EXISTS public.invitation_campaigns (
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

CREATE TABLE IF NOT EXISTS public.candidate_submissions (
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

COMMIT;

-- STEP 6: Verify tables were created
SELECT 
    'public.candidate_submissions exists' as check,
    EXISTS (
        SELECT FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename = 'candidate_submissions'
    ) as result
UNION ALL
SELECT 
    'public.invitation_campaigns exists' as check,
    EXISTS (
        SELECT FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename = 'invitation_campaigns'
    ) as result;

-- STEP 7: If tables still don't exist, check for errors
-- Run this to see recent errors:
SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction' AND query LIKE '%candidate_submissions%';

-- STEP 8: Grant permissions (if needed)
GRANT ALL ON TABLE public.candidate_submissions TO CURRENT_USER;
GRANT ALL ON TABLE public.invitation_campaigns TO CURRENT_USER;