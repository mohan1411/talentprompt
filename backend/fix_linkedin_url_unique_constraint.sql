-- Remove the unique constraint on linkedin_url to allow multiple users to import the same profile
-- Instead, we'll create a unique constraint on (user_id, linkedin_url) combination

-- First, drop the existing unique constraint
ALTER TABLE resumes DROP CONSTRAINT IF EXISTS resumes_linkedin_url_key;

-- Create a new unique constraint on the combination of user_id and linkedin_url
-- This ensures each user can only import a profile once, but multiple users can import the same profile
ALTER TABLE resumes ADD CONSTRAINT resumes_user_id_linkedin_url_key UNIQUE (user_id, linkedin_url);

-- Add an index on linkedin_url for performance (since we still query by it)
CREATE INDEX IF NOT EXISTS idx_resumes_linkedin_url ON resumes(linkedin_url);