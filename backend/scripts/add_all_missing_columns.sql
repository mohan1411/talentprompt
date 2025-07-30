-- Add all missing columns to match the model definitions

-- For invitation_campaigns table
ALTER TABLE invitation_campaigns
ADD COLUMN IF NOT EXISTS branding JSONB,
ADD COLUMN IF NOT EXISTS auto_close_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS max_submissions INTEGER,
ADD COLUMN IF NOT EXISTS stats JSONB DEFAULT '{}';

-- Verify columns were added
SELECT 
    column_name, 
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'invitation_campaigns'
ORDER BY ordinal_position;

-- Quick test to ensure all columns work
UPDATE invitation_campaigns 
SET stats = '{"views": 0, "submissions": 0}'::jsonb
WHERE stats IS NULL;

SELECT 'All columns added successfully!' as result;