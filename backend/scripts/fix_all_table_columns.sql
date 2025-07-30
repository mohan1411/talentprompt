-- Comprehensive fix for all missing columns

-- First check current state
SELECT 'CURRENT invitation_campaigns COLUMNS:' as info;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'invitation_campaigns'
ORDER BY ordinal_position;

SELECT 'CURRENT candidate_submissions COLUMNS:' as info;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'candidate_submissions'
ORDER BY ordinal_position;

-- Add missing columns to invitation_campaigns
ALTER TABLE invitation_campaigns
ADD COLUMN IF NOT EXISTS branding JSONB,
ADD COLUMN IF NOT EXISTS auto_close_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS max_submissions INTEGER,
ADD COLUMN IF NOT EXISTS stats JSONB DEFAULT '{}';

-- Add missing columns to candidate_submissions (if any)
ALTER TABLE candidate_submissions
ADD COLUMN IF NOT EXISTS phone VARCHAR(50),
ADD COLUMN IF NOT EXISTS resume_file_url VARCHAR(500);

-- Also add the expires_in_days column to campaigns if missing
ALTER TABLE invitation_campaigns
ADD COLUMN IF NOT EXISTS expires_in_days INTEGER DEFAULT 7;

-- Update any null stats to empty object
UPDATE invitation_campaigns SET stats = '{}' WHERE stats IS NULL;

-- Verify all columns exist
SELECT 'AFTER FIX - invitation_campaigns:' as info;
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_name = 'invitation_campaigns'
ORDER BY ordinal_position;

SELECT 'AFTER FIX - candidate_submissions:' as info;
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_name = 'candidate_submissions'
ORDER BY ordinal_position;

-- Test that everything works
INSERT INTO invitation_campaigns (
    recruiter_id, 
    name,
    stats,
    branding
) VALUES (
    gen_random_uuid(),
    'Test Campaign',
    '{"views": 0}'::jsonb,
    '{"logo": null}'::jsonb
) RETURNING id;

-- Clean up test
DELETE FROM invitation_campaigns WHERE name = 'Test Campaign';

SELECT '✅ All columns fixed successfully!' as result;