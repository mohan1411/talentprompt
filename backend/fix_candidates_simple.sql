-- Simplified fix for local environment
-- This avoids complex DO blocks that can cause parsing issues

-- 1. Create the candidates table
CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    current_title VARCHAR(255),
    current_company VARCHAR(255),
    years_of_experience FLOAT,
    skills TEXT[],
    education JSONB,
    experience JSONB,
    location VARCHAR(255),
    linkedin_url VARCHAR(500),
    github_url VARCHAR(500),
    portfolio_url VARCHAR(500),
    availability VARCHAR(100),
    salary_expectation VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create indexes
CREATE INDEX IF NOT EXISTS idx_candidates_resume_id ON candidates(resume_id);
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(first_name, last_name);

-- 3. Try to add unique constraint (ignore error if exists)
ALTER TABLE candidates ADD CONSTRAINT unique_resume_id UNIQUE (resume_id);

-- 4. Populate candidates from resumes
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
    r.id as resume_id,
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

-- 5. Show summary
SELECT 'Setup complete!' as message,
       (SELECT COUNT(*) FROM candidates) as total_candidates,
       (SELECT COUNT(*) FROM resumes) as total_resumes;