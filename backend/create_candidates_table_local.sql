-- Migration script for LOCAL environment only
-- DO NOT RUN IN PRODUCTION (already exists there)

-- Create candidates table if it doesn't exist
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_candidates_resume_id ON candidates(resume_id);
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(first_name, last_name);

-- Create a unique constraint on resume_id (one candidate per resume)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'unique_resume_id'
    ) THEN
        ALTER TABLE candidates 
        ADD CONSTRAINT unique_resume_id UNIQUE (resume_id);
    END IF;
END $$;

-- Populate candidates table from existing resumes
-- This will create a candidate record for each resume
INSERT INTO candidates (
    resume_id,
    first_name,
    last_name,
    email,
    phone,
    current_title,
    current_company,
    years_of_experience,
    skills,
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
    r.current_company,
    CASE 
        WHEN r.years_experience IS NOT NULL THEN r.years_experience::FLOAT
        ELSE NULL
    END as years_of_experience,
    CASE 
        WHEN r.skills IS NOT NULL THEN 
            CASE 
                WHEN jsonb_typeof(r.skills) = 'array' THEN 
                    ARRAY(SELECT jsonb_array_elements_text(r.skills))
                ELSE 
                    ARRAY[r.skills::text]
            END
        ELSE 
            ARRAY[]::TEXT[]
    END as skills,
    r.location,
    r.created_at,
    r.updated_at
FROM resumes r
WHERE NOT EXISTS (
    SELECT 1 FROM candidates c WHERE c.resume_id = r.id
);

-- Update candidate_pipeline_states to use candidate IDs
-- First, update any pipeline states that reference resume_ids to use candidate_ids
DO $$
DECLARE
    rec RECORD;
BEGIN
    -- Check if candidate_pipeline_states references candidates correctly
    FOR rec IN 
        SELECT DISTINCT cps.candidate_id as old_id
        FROM candidate_pipeline_states cps
        WHERE cps.candidate_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM candidates c WHERE c.id = cps.candidate_id
        )
    LOOP
        -- Check if this ID is actually a resume_id
        IF EXISTS (SELECT 1 FROM resumes WHERE id = rec.old_id) THEN
            -- Get or create the candidate for this resume
            INSERT INTO candidates (resume_id, first_name, last_name, email, current_title, location)
            SELECT id, first_name, last_name, email, current_title, location
            FROM resumes 
            WHERE id = rec.old_id
            ON CONFLICT (resume_id) DO NOTHING;
            
            -- Update the pipeline state to use the correct candidate_id
            UPDATE candidate_pipeline_states 
            SET candidate_id = (SELECT id FROM candidates WHERE resume_id = rec.old_id)
            WHERE candidate_id = rec.old_id;
        END IF;
    END LOOP;
END $$;

-- Verify the tables are properly linked
DO $$
BEGIN
    RAISE NOTICE 'Candidates table created/updated successfully';
    RAISE NOTICE 'Total candidates: %', (SELECT COUNT(*) FROM candidates);
    RAISE NOTICE 'Total resumes: %', (SELECT COUNT(*) FROM resumes);
    RAISE NOTICE 'Pipeline states with valid candidates: %', 
        (SELECT COUNT(*) FROM candidate_pipeline_states cps 
         WHERE EXISTS (SELECT 1 FROM candidates c WHERE c.id = cps.candidate_id));
END $$;