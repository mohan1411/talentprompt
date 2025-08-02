-- Complete fix for candidate_notes table

-- 1. First, see what columns currently exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'candidate_notes'
ORDER BY ordinal_position;

-- 2. Check if the table has wrong column names
-- Maybe it has 'content' or 'text' instead of 'note'
SELECT * FROM candidate_notes LIMIT 1;

-- 3. Fix the table structure completely
-- Option A: If table has a different column name for the note content, rename it
DO $$
BEGIN
    -- Check if 'content' exists and 'note' doesn't
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'candidate_notes' AND column_name = 'content')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name = 'candidate_notes' AND column_name = 'note') THEN
        ALTER TABLE candidate_notes RENAME COLUMN content TO note;
    -- Check if 'text' exists and 'note' doesn't
    ELSIF EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'candidate_notes' AND column_name = 'text')
          AND NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'candidate_notes' AND column_name = 'note') THEN
        ALTER TABLE candidate_notes RENAME COLUMN text TO note;
    -- Check if 'comment' exists and 'note' doesn't
    ELSIF EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'candidate_notes' AND column_name = 'comment')
          AND NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'candidate_notes' AND column_name = 'note') THEN
        ALTER TABLE candidate_notes RENAME COLUMN comment TO note;
    END IF;
END $$;

-- 4. Add 'note' column if it still doesn't exist
ALTER TABLE candidate_notes 
ADD COLUMN IF NOT EXISTS note TEXT;

-- 5. Ensure all required columns exist
ALTER TABLE candidate_notes 
ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid() PRIMARY KEY;

ALTER TABLE candidate_notes 
ADD COLUMN IF NOT EXISTS pipeline_state_id UUID REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE;

ALTER TABLE candidate_notes 
ADD COLUMN IF NOT EXISTS note TEXT;

ALTER TABLE candidate_notes 
ADD COLUMN IF NOT EXISTS is_private BOOLEAN DEFAULT FALSE;

ALTER TABLE candidate_notes 
ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);

ALTER TABLE candidate_notes 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE candidate_notes 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 6. Verify final structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'candidate_notes'
ORDER BY ordinal_position;