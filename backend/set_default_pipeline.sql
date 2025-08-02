-- Set the "TalentPrompt" pipeline as the default pipeline
UPDATE pipelines 
SET is_default = true 
WHERE id = 'e67f54a1-84b7-432c-b8ab-8e00223a38f2';

-- Or if you prefer to set the first pipeline as default:
-- UPDATE pipelines 
-- SET is_default = true 
-- WHERE id = (SELECT id FROM pipelines ORDER BY created_at LIMIT 1);

-- Verify the change:
-- SELECT id, name, is_default FROM pipelines;