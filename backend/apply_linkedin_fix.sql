-- Since the unique constraint is already removed, let's just add the new one

-- Add user-specific unique constraint
-- This ensures each user can only import a profile once, but multiple users can import the same profile
ALTER TABLE resumes ADD CONSTRAINT resumes_user_id_linkedin_url_key UNIQUE (user_id, linkedin_url);

-- Add index on linkedin_url for performance (since we still query by it)
CREATE INDEX IF NOT EXISTS idx_resumes_linkedin_url ON resumes(linkedin_url);

-- Verify the constraints
SELECT conname, contype, conkey 
FROM pg_constraint 
WHERE conrelid = 'resumes'::regclass 
AND conname LIKE '%linkedin%';