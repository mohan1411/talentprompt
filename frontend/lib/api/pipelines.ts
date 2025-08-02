import { apiClient } from './client'

export interface PipelineStage {
  id: string
  name: string
  order: number
  color: string
  type?: string
  actions?: string[]
}

export interface Pipeline {
  id: string
  name: string
  description?: string
  stages: PipelineStage[]
  team_id?: string
  is_default: boolean
  is_active: boolean
  created_by: string
  created_at: string
  updated_at: string
}

export interface PipelineCreate {
  name: string
  description?: string
  stages: PipelineStage[]
  team_id?: string
  is_default?: boolean
}

export interface PipelineUpdate {
  name?: string
  description?: string
  stages?: PipelineStage[]
  team_id?: string
  is_default?: boolean
}

export interface CandidateJourney {
  id: string
  resume_id: string
  pipeline_id: string
  job_position: string
  status: string
  current_stage?: string
  completed_stages: string[]
  stage_results: Record<string, any>
  overall_score?: number
  final_recommendation?: string
  started_at: string
  completed_at?: string
  updated_at: string
}

export interface CandidateProgress {
  journey_id: string
  candidate_name: string
  job_position: string
  pipeline_name: string
  current_stage: string
  progress_percentage: number
  completed_stages: number
  total_stages: number
  overall_score?: number
  status: string
  last_activity: string
  next_action?: string
}

export const pipelineApi = {
  // Pipeline management
  async createPipeline(data: PipelineCreate): Promise<Pipeline> {
    const response = await apiClient.post('/workflow/', data)
    return response.data
  },

  async getPipelines(params?: {
    skip?: number
    limit?: number
    job_role?: string
    is_active?: boolean
  }): Promise<Pipeline[]> {
    const response = await apiClient.get('/workflow/', { params })
    return response.data
  },

  async getPipeline(id: string): Promise<Pipeline> {
    const response = await apiClient.get(`/workflow/${id}`)
    return response.data
  },

  async updatePipeline(id: string, data: PipelineUpdate): Promise<Pipeline> {
    const response = await apiClient.put(`/workflow/${id}`, data)
    return response.data
  },

  // Candidate journey management
  async startJourney(data: {
    resume_id: string
    pipeline_id: string
    job_position: string
  }): Promise<CandidateJourney> {
    const response = await apiClient.post('/pipelines/journeys', data)
    return response.data
  },

  async getCandidateJourneys(resumeId: string): Promise<CandidateJourney[]> {
    const response = await apiClient.get(`/pipelines/journeys/candidate/${resumeId}`)
    return response.data
  },

  async completeStage(journeyId: string, sessionId: string): Promise<CandidateJourney> {
    const response = await apiClient.post(
      `/pipelines/journeys/${journeyId}/complete-stage?session_id=${sessionId}`,
      null
    )
    return response.data
  },

  // Progress dashboard
  async getProgressDashboard(params?: {
    status?: string
    pipeline_id?: string
  }): Promise<CandidateProgress[]> {
    const response = await apiClient.get('/pipelines/progress/dashboard', { params })
    return response.data
  }
}