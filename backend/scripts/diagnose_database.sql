-- COMPREHENSIVE DATABASE DIAGNOSTIC
-- Run each section one by one in pgAdmin

-- 1. WHERE AM I CONNECTED?
SELECT 
    current_database() as database,
    current_user as user,
    current_schema() as schema,
    version() as postgres_version;

-- 2. WHAT SCHEMAS EXIST?
SELECT schema_name 
FROM information_schema.schemata 
ORDER BY schema_name;

-- 3. WHAT'S MY SEARCH PATH?
SHOW search_path;

-- 4. DO TABLES EXIST IN ANY SCHEMA?
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename IN ('candidate_submissions', 'invitation_campaigns')
ORDER BY schemaname, tablename;

-- 5. CHECK ALL TABLES IN ALL SCHEMAS
SELECT 
    table_schema,
    table_name
FROM information_schema.tables 
WHERE table_name IN ('candidate_submissions', 'invitation_campaigns')
ORDER BY table_schema, table_name;

-- 6. WHAT TABLES EXIST IN PUBLIC SCHEMA?
SELECT 
    tablename,
    tableowner,
    hasindexes,
    hasrules,
    hastriggers
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- 7. CHECK USER PERMISSIONS
SELECT 
    has_database_privilege(current_user, current_database(), 'CREATE') as can_create_in_db,
    has_schema_privilege(current_user, 'public', 'CREATE') as can_create_in_public,
    has_schema_privilege(current_user, 'public', 'USAGE') as can_use_public;

-- 8. TRY CREATING IN SPECIFIC SCHEMA
-- First set search path
SET search_path TO public;

-- Create a test table
CREATE TABLE public.test_permissions (
    id SERIAL PRIMARY KEY,
    test VARCHAR(50)
);

-- Check if it was created
SELECT 
    schemaname,
    tablename 
FROM pg_tables 
WHERE tablename = 'test_permissions';

-- Drop test table
DROP TABLE IF EXISTS public.test_permissions;

-- 9. CHECK FOR NAME CONFLICTS
SELECT 
    n.nspname as schema,
    c.relname as name,
    CASE c.relkind
        WHEN 'r' THEN 'table'
        WHEN 'v' THEN 'view'
        WHEN 'm' THEN 'materialized view'
        WHEN 'i' THEN 'index'
        WHEN 'S' THEN 'sequence'
        WHEN 's' THEN 'special'
        WHEN 'f' THEN 'foreign table'
        WHEN 'p' THEN 'partitioned table'
        WHEN 'I' THEN 'partitioned index'
    END as type
FROM pg_catalog.pg_class c
LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE c.relname IN ('candidate_submissions', 'invitation_campaigns')
ORDER BY 1,2;

-- 10. FORCE CREATE WITH EXPLICIT SCHEMA
BEGIN;

-- Drop if exists
DROP TABLE IF EXISTS public.candidate_submissions CASCADE;
DROP TABLE IF EXISTS public.invitation_campaigns CASCADE;

-- Create with explicit schema
CREATE TABLE public.invitation_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE public.candidate_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(255) UNIQUE NOT NULL,
    recruiter_id UUID NOT NULL,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Verify
SELECT 
    'Tables created in transaction' as status,
    schemaname,
    tablename 
FROM pg_tables 
WHERE tablename IN ('candidate_submissions', 'invitation_campaigns')
AND schemaname = 'public';

COMMIT;

-- 11. FINAL VERIFICATION
SELECT 
    'FINAL CHECK' as check_type,
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename IN ('candidate_submissions', 'invitation_campaigns');