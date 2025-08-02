-- Check and fix candidate data issues

-- 1. First, let's see if we have any candidates at all
SELECT COUNT(*) as total_candidates FROM candidates;
SELECT COUNT(*) as total_resumes FROM resumes;

-- 2. Check if there are any resumes without corresponding candidates
SELECT COUNT(*) as resumes_without_candidates
FROM resumes r
WHERE NOT EXISTS (
    SELECT 1 FROM candidates c WHERE c.resume_id = r.id
);

-- 3. Create missing candidates from resumes
INSERT INTO candidates (
    resume_id,
    first_name,
    last_name,
    email,
    phone,
    current_title,
    location,
    created_at,
    updated_at
)
SELECT 
    r.id,
    r.first_name,
    r.last_name,
    r.email,
    r.phone,
    r.current_title,
    r.location,
    r.created_at,
    r.updated_at
FROM resumes r
WHERE NOT EXISTS (
    SELECT 1 FROM candidates c WHERE c.resume_id = r.id
);

-- 4. Check if we're using resume IDs where we should use candidate IDs
-- This will show any orphaned pipeline states
SELECT 
    cps.id,
    cps.candidate_id,
    CASE 
        WHEN c.id IS NULL AND r.id IS NOT NULL THEN 'Using Resume ID instead of Candidate ID'
        WHEN c.id IS NULL AND r.id IS NULL THEN 'Invalid ID - not found'
        ELSE 'Valid Candidate ID'
    END as status
FROM candidate_pipeline_states cps
LEFT JOIN candidates c ON c.id = cps.candidate_id
LEFT JOIN resumes r ON r.id = cps.candidate_id
LIMIT 10;

-- 5. Fix pipeline states that are using resume_id instead of candidate_id
UPDATE candidate_pipeline_states cps
SET candidate_id = c.id
FROM candidates c
WHERE cps.candidate_id NOT IN (SELECT id FROM candidates)
  AND cps.candidate_id IN (SELECT id FROM resumes)
  AND c.resume_id = cps.candidate_id;

-- 6. Show summary after fixes
SELECT 
    'Total Candidates' as metric, COUNT(*) as count FROM candidates
UNION ALL
SELECT 'Total Resumes', COUNT(*) FROM resumes
UNION ALL
SELECT 'Valid Pipeline States', COUNT(*) 
FROM candidate_pipeline_states cps
WHERE EXISTS (SELECT 1 FROM candidates c WHERE c.id = cps.candidate_id)
UNION ALL
SELECT 'Invalid Pipeline States', COUNT(*) 
FROM candidate_pipeline_states cps
WHERE NOT EXISTS (SELECT 1 FROM candidates c WHERE c.id = cps.candidate_id);