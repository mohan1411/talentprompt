// Pipeline and workflow management types

export interface PipelineStage {
  id: string;
  name: string;
  order: number;
  color: string;
  type?: string;
  actions?: string[];
}

export interface Pipeline {
  id: string;
  name: string;
  description?: string;
  stages: PipelineStage[];
  team_id?: string;
  is_default: boolean;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface CandidateInPipeline {
  id: string;
  pipeline_state_id: string;
  first_name: string;
  last_name: string;
  email?: string;
  current_title?: string;
  current_stage: string;
  time_in_stage: number;
  assigned_to?: {
    id: string;
    name: string;
  };
  tags: string[];
  entered_stage_at: string;
  is_active: boolean;
}

export interface PipelineActivity {
  id: string;
  type: string;
  user: {
    id: string;
    name: string;
  };
  from_stage?: string;
  to_stage?: string;
  details?: any;
  content?: string;
  created_at: string;
}

export interface CandidateNote {
  id: string;
  content: string;
  is_private: boolean;
  user: {
    id: string;
    name: string;
  };
  mentioned_users: string[];
  created_at: string;
  updated_at: string;
}

export interface CandidateEvaluation {
  id: string;
  stage_id: string;
  rating?: number;
  recommendation?: 'strong_yes' | 'yes' | 'neutral' | 'no' | 'strong_no';
  strengths?: string;
  concerns?: string;
  evaluator: {
    id: string;
    name: string;
  };
  created_at: string;
}

export interface PipelineAnalytics {
  stage_distribution: Record<string, number>;
  avg_time_in_stage: Record<string, number>;
  total_candidates: number;
  active_candidates: number;
}

// Request types
export interface CreatePipelineRequest {
  name: string;
  description?: string;
  stages: PipelineStage[];
  team_id?: string;
  is_default?: boolean;
}

export interface AddCandidateToPipelineRequest {
  candidate_id: string;
  pipeline_id: string;
  assigned_to?: string;
  stage_id?: string;
}

export interface MoveCandidateRequest {
  new_stage_id: string;
  reason?: string;
}

export interface AddNoteRequest {
  content: string;
  is_private?: boolean;
  mentioned_users?: string[];
}

export interface AddEvaluationRequest {
  stage_id: string;
  rating?: number;
  recommendation?: 'strong_yes' | 'yes' | 'neutral' | 'no' | 'strong_no';
  strengths?: string;
  concerns?: string;
  technical_assessment?: any;
  cultural_fit_assessment?: any;
  would_work_with?: boolean;
  interview_id?: string;
}