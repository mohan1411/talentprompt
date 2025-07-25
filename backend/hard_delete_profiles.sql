-- Alternative: Actually DELETE profiles instead of soft delete

-- Delete your soft-deleted profiles permanently
DELETE FROM resumes
WHERE user_id = 'd48c0d47-d6d3-404b-9f58-8552534f9b4d'
AND status = 'deleted';

-- Verify they're gone
SELECT COUNT(*) as deleted_count
FROM resumes
WHERE user_id = 'd48c0d47-d6d3-404b-9f58-8552534f9b4d'
AND status = 'deleted';