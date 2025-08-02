-- Simple fix for local environment - creates candidates table and populates from resumes
-- Run this in pgAdmin or psql

-- Step 1: Create the candidates table
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

-- Step 2: Create indexes
CREATE INDEX IF NOT EXISTS idx_candidates_resume_id ON candidates(resume_id);
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);

-- Step 3: Populate from resumes (only if not already exists)
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

-- Step 4: Show results
SELECT 
    'Candidates created' as status,
    COUNT(*) as count 
FROM candidates
UNION ALL
SELECT 
    'Resumes total' as status,
    COUNT(*) as count 
FROM resumes;