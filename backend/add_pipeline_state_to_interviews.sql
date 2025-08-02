-- Add pipeline_state_id to interview_sessions table
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS pipeline_state_id UUID REFERENCES candidate_pipeline_states(id);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_interview_sessions_pipeline_state_id 
ON interview_sessions(pipeline_state_id);

-- Add foreign key constraint
ALTER TABLE interview_sessions
ADD CONSTRAINT fk_interview_sessions_pipeline_state
FOREIGN KEY (pipeline_state_id) 
REFERENCES candidate_pipeline_states(id)
ON DELETE SET NULL;