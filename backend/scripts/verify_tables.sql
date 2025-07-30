-- Run this in pgAdmin to verify tables exist

-- 1. List all tables in public schema
SELECT 
    table_name,
    CASE 
        WHEN table_name IN ('candidate_submissions', 'invitation_campaigns') 
        THEN '✅ REQUIRED TABLE'
        ELSE '📋 Other table'
    END as status
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY 
    CASE WHEN table_name IN ('candidate_submissions', 'invitation_campaigns') THEN 0 ELSE 1 END,
    table_name;

-- 2. Check specific tables
SELECT 
    'candidate_submissions' as table_name,
    EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'candidate_submissions'
    ) as exists,
    CASE 
        WHEN EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'candidate_submissions'
        ) THEN '✅ Table exists!'
        ELSE '❌ Table missing!'
    END as status
UNION ALL
SELECT 
    'invitation_campaigns' as table_name,
    EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'invitation_campaigns'
    ) as exists,
    CASE 
        WHEN EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'invitation_campaigns'
        ) THEN '✅ Table exists!'
        ELSE '❌ Table missing!'
    END as status;

-- 3. If tables exist, show their structure
SELECT 
    c.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    CASE 
        WHEN tc.constraint_type = 'PRIMARY KEY' THEN 'PK'
        WHEN tc.constraint_type = 'FOREIGN KEY' THEN 'FK'
        WHEN tc.constraint_type = 'UNIQUE' THEN 'UQ'
        ELSE ''
    END as constraint
FROM information_schema.columns c
LEFT JOIN information_schema.key_column_usage kcu 
    ON c.table_name = kcu.table_name 
    AND c.column_name = kcu.column_name
LEFT JOIN information_schema.table_constraints tc 
    ON kcu.constraint_name = tc.constraint_name
WHERE c.table_name IN ('candidate_submissions', 'invitation_campaigns')
AND c.table_schema = 'public'
ORDER BY c.table_name, c.ordinal_position;