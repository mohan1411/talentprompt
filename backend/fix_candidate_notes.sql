-- Fix candidate_notes table - add missing columns

-- 1. Check current structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'candidate_notes'
ORDER BY ordinal_position;

-- 2. Add missing columns
ALTER TABLE candidate_notes 
ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);

ALTER TABLE candidate_notes 
ADD COLUMN IF NOT EXISTS is_private BOOLEAN DEFAULT FALSE;

ALTER TABLE candidate_notes 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 3. Verify the changes
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'candidate_notes'
WHERE column_name IN ('created_by', 'is_private', 'updated_at', 'note')
ORDER BY column_name;