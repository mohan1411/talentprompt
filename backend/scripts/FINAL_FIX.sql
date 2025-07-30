-- FINAL FIX - RUN THIS ENTIRE SCRIPT IN PGADMIN
-- This handles all possible edge cases

-- 1. Set search path explicitly
SET search_path TO public, pg_catalog;

-- 2. Show current state
DO $$
BEGIN
    RAISE NOTICE 'Current database: %', current_database();
    RAISE NOTICE 'Current user: %', current_user;
    RAISE NOTICE 'Current schema: %', current_schema();
END $$;

-- 3. Drop tables in all possible schemas
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Find and drop candidate_submissions in any schema
    FOR r IN (
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE tablename = 'candidate_submissions'
    ) LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I.%I CASCADE', r.schemaname, r.tablename);
        RAISE NOTICE 'Dropped %.%', r.schemaname, r.tablename;
    END LOOP;
    
    -- Find and drop invitation_campaigns in any schema
    FOR r IN (
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE tablename = 'invitation_campaigns'
    ) LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I.%I CASCADE', r.schemaname, r.tablename);
        RAISE NOTICE 'Dropped %.%', r.schemaname, r.tablename;
    END LOOP;
END $$;

-- 4. Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS public;

-- 5. Grant permissions
GRANT ALL ON SCHEMA public TO CURRENT_USER;

-- 6. Create tables with absolute path
CREATE TABLE public.invitation_campaigns (
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

CREATE TABLE public.candidate_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(255) UNIQUE NOT NULL,
    submission_type VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    recruiter_id UUID NOT NULL,
    campaign_id UUID REFERENCES public.invitation_campaigns(id),
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

-- 7. Create indexes
CREATE INDEX ix_candidate_submissions_token ON public.candidate_submissions(token);
CREATE INDEX ix_candidate_submissions_recruiter_id ON public.candidate_submissions(recruiter_id);
CREATE INDEX ix_candidate_submissions_email ON public.candidate_submissions(email);

-- 8. Grant permissions on tables
GRANT ALL ON TABLE public.candidate_submissions TO CURRENT_USER;
GRANT ALL ON TABLE public.invitation_campaigns TO CURRENT_USER;

-- 9. Verify creation with detailed info
SELECT 
    'VERIFICATION RESULTS' as section,
    '===================' as separator;

SELECT 
    n.nspname as schema,
    c.relname as table_name,
    pg_catalog.pg_get_userbyid(c.relowner) as owner,
    pg_catalog.pg_size_pretty(pg_catalog.pg_table_size(c.oid)) as size,
    c.reltuples::bigint as row_count
FROM pg_catalog.pg_class c
LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE c.relname IN ('candidate_submissions', 'invitation_campaigns')
AND c.relkind = 'r'
ORDER BY 1,2;

-- 10. Test insert
BEGIN;
INSERT INTO public.invitation_campaigns (recruiter_id, name) 
VALUES (gen_random_uuid(), 'Test Campaign');

INSERT INTO public.candidate_submissions (
    token, submission_type, status, recruiter_id, email, expires_at
) VALUES (
    'test_token_' || gen_random_uuid(), 
    'new', 
    'pending', 
    gen_random_uuid(), 
    'test@example.com', 
    CURRENT_TIMESTAMP + INTERVAL '7 days'
);

SELECT 'INSERT TEST PASSED' as result;
ROLLBACK;

-- 11. Final check
SELECT 
    CASE 
        WHEN COUNT(*) = 2 THEN '✅ SUCCESS: Both tables exist in public schema!'
        ELSE '❌ FAILED: Tables not created properly'
    END as final_status,
    COUNT(*) as tables_found
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('candidate_submissions', 'invitation_campaigns');

-- 12. Show connection info for app
SELECT 
    'APP CONNECTION INFO' as section,
    '===================' as separator;

SELECT 
    'Make sure your app DATABASE_URL uses:' as instruction,
    current_database() as database,
    current_user as user,
    'public' as schema_to_use;