-- Add rejected and withdrawn stages to existing pipelines
UPDATE pipelines
SET stages = jsonb_set(
    jsonb_set(
        stages,
        '{5}',
        '{"id": "rejected", "name": "Rejected", "order": 6, "color": "#ef4444", "type": "final", "actions": []}'::jsonb,
        true
    ),
    '{6}',
    '{"id": "withdrawn", "name": "Withdrawn", "order": 7, "color": "#6b7280", "type": "final", "actions": []}'::jsonb,
    true
),
updated_at = NOW()
WHERE is_default = true
  AND NOT (stages @> '[{"id": "rejected"}]'::jsonb);

-- Verify the update
SELECT name, jsonb_array_length(stages) as stage_count, stages
FROM pipelines 
WHERE is_default = true;