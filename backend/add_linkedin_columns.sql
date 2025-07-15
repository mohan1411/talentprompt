-- Add LinkedIn columns to resumes table if they don't exist
ALTER TABLE resumes 
ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR UNIQUE,
ADD COLUMN IF NOT EXISTS linkedin_data JSON,
ADD COLUMN IF NOT EXISTS last_linkedin_sync TIMESTAMP WITH TIME ZONE;

-- Create index on linkedin_url
CREATE INDEX IF NOT EXISTS ix_resumes_linkedin_url ON resumes(linkedin_url);

-- Create LinkedIn import history table if it doesn't exist
CREATE TABLE IF NOT EXISTS linkedin_import_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    resume_id UUID REFERENCES resumes(id),
    linkedin_url VARCHAR NOT NULL,
    import_status VARCHAR NOT NULL,
    error_message TEXT,
    raw_data JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source VARCHAR
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_linkedin_import_history_user_id ON linkedin_import_history(user_id);
CREATE INDEX IF NOT EXISTS ix_linkedin_import_history_created_at ON linkedin_import_history(created_at);