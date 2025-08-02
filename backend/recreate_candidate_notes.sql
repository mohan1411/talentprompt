-- Recreate candidate_notes table with correct structure

-- 1. Drop the existing table
DROP TABLE IF EXISTS candidate_notes CASCADE;

-- 2. Create with correct structure
CREATE TABLE candidate_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_state_id UUID REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
    note TEXT NOT NULL,
    is_private BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create indexes for performance
CREATE INDEX idx_candidate_notes_pipeline_state ON candidate_notes(pipeline_state_id);
CREATE INDEX idx_candidate_notes_created_by ON candidate_notes(created_by);
CREATE INDEX idx_candidate_notes_created_at ON candidate_notes(created_at DESC);

-- 4. Verify the structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'candidate_notes'
ORDER BY ordinal_position;