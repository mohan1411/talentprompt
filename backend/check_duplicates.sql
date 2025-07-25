-- Check if there are any duplicate linkedin_urls in the database
-- This might be preventing the unique constraint from being created

-- Find all duplicate linkedin_urls
SELECT linkedin_url, COUNT(*) as count, array_agg(user_id) as user_ids
FROM resumes
WHERE linkedin_url IS NOT NULL
GROUP BY linkedin_url
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC;

-- Check if the new constraint exists
SELECT conname, contype
FROM pg_constraint
WHERE conrelid = 'resumes'::regclass
AND conname = 'resumes_user_id_linkedin_url_key';

-- Check what constraints currently exist on the resumes table
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'resumes'::regclass
ORDER BY conname;