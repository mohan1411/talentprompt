-- Insert a default pipeline if none exists
-- This version doesn't use DO block for better pgAdmin compatibility

-- First, run this query to check if a default pipeline already exists:
-- SELECT * FROM pipelines WHERE is_default = true;

-- If no rows are returned, run this insert:
INSERT INTO pipelines (
    name,
    description,
    stages,
    team_id,
    is_default,
    is_active,
    created_by,
    created_at,
    updated_at
) 
SELECT 
    'Default Hiring Pipeline',
    'Standard hiring workflow for all positions',
    '[
        {
            "id": "applied",
            "name": "Applied",
            "order": 1,
            "color": "#9ca3af",
            "type": "initial",
            "actions": ["review", "reject"]
        },
        {
            "id": "screening",
            "name": "Screening",
            "order": 2,
            "color": "#3b82f6",
            "type": "review",
            "actions": ["schedule_interview", "reject", "move_to_interview"]
        },
        {
            "id": "interview",
            "name": "Interview",
            "order": 3,
            "color": "#8b5cf6",
            "type": "interview",
            "actions": ["schedule_next", "reject", "move_to_offer"]
        },
        {
            "id": "offer",
            "name": "Offer",
            "order": 4,
            "color": "#f59e0b",
            "type": "decision",
            "actions": ["send_offer", "negotiate", "reject"]
        },
        {
            "id": "hired",
            "name": "Hired",
            "order": 5,
            "color": "#10b981",
            "type": "final",
            "actions": ["onboard"]
        }
    ]'::jsonb,
    NULL, -- Global pipeline (no team)
    true, -- is_default
    true, -- is_active
    (SELECT id FROM users WHERE is_superuser = true LIMIT 1),
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM pipelines WHERE is_default = true
);