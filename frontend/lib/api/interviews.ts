import { apiClient } from './client'

export interface InterviewSession {
  id: string
  resume_id: string
  interviewer_id: string
  job_position: string
  job_requirements?: any
  interview_type?: 'IN_PERSON' | 'VIRTUAL' | 'PHONE'  // Mode
  interview_category?: string  // general, technical, behavioral, final
  scheduled_at?: string
  duration_minutes?: number
  status: 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'PROCESSING'
  started_at?: string
  ended_at?: string
  preparation_notes?: any
  suggested_questions?: any[]
  transcript?: string
  transcript_data?: any
  notes?: string
  recordings?: any[]
  scorecard?: any
  overall_rating?: number
  recommendation?: string
  strengths?: string[]
  concerns?: string[]
  created_at: string
  updated_at: string
  questions?: InterviewQuestion[]
}

export interface InterviewQuestion {
  id: string
  session_id: string
  question_text: string
  category: string
  difficulty_level: number
  ai_generated: boolean
  generation_context?: string
  expected_answer_points?: string[]
  follow_up_questions?: string[]
  order_index: number
  asked: boolean
  asked_at?: string
  response_summary?: string
  response_rating?: number
  response_notes?: string
  created_at: string
  updated_at: string
}

export interface InterviewPreparationRequest {
  resume_id: string
  job_position: string
  job_requirements?: any
  interview_type?: 'IN_PERSON' | 'VIRTUAL' | 'PHONE' | null  // Mode
  interview_category: string  // general, technical, behavioral, final
  pipeline_state_id?: string  // Link to pipeline state if coming from pipeline view
  difficulty_level: number
  num_questions: number
  focus_areas?: string[]
  company_culture?: string
}

export interface InterviewPreparationResponse {
  session_id: string
  candidate_summary: any
  key_talking_points: string[]
  areas_to_explore: string[]
  red_flags: string[]
  suggested_questions: InterviewQuestion[]
  interview_structure: any
  estimated_duration: number
}

export interface InterviewScorecardResponse {
  session_id: string
  candidate_name: string
  position: string
  interview_date: string
  overall_rating: number
  recommendation: string
  technical_skills: Record<string, number>
  soft_skills: Record<string, number>
  culture_fit: number
  strengths: string[]
  concerns: string[]
  next_steps: string[]
  interviewer_notes: string
  key_takeaways: string[]
  percentile_rank?: number
  similar_candidates?: any[]
}

export const interviewsApi = {
  // Prepare for an interview
  async prepareInterview(data: InterviewPreparationRequest): Promise<InterviewPreparationResponse> {
    return await apiClient.post('/interviews/prepare', data)
  },

  // Get all interview sessions
  async getSessions(params?: { skip?: number; limit?: number; status?: string }): Promise<InterviewSession[]> {
    return await apiClient.get('/interviews/sessions', { params })
  },

  // Get a specific interview session
  async getSession(sessionId: string): Promise<InterviewSession> {
    return await apiClient.get(`/interviews/sessions/${sessionId}`)
  },

  // Update an interview session
  async updateSession(sessionId: string, data: Partial<InterviewSession>): Promise<InterviewSession> {
    return await apiClient.patch(`/interviews/sessions/${sessionId}`, data)
  },

  // Generate additional questions
  async generateMoreQuestions(sessionId: string, data: {
    num_questions: number
    category?: string
    difficulty_level?: number
    context?: string
  }): Promise<InterviewQuestion[]> {
    return await apiClient.post(`/interviews/sessions/${sessionId}/questions`, data)
  },

  // Update question response
  async updateQuestionResponse(questionId: string, data: {
    asked?: boolean
    response_summary?: string
    response_rating?: number
    response_notes?: string
  }): Promise<InterviewQuestion> {
    return await apiClient.put(`/interviews/questions/${questionId}/response`, data)
  },

  // Add interview feedback
  async addFeedback(sessionId: string, data: {
    overall_rating: number
    recommendation: string
    strengths: string[]
    concerns: string[]
    technical_assessment?: string
    cultural_fit_assessment?: string
    additional_notes?: string
  }): Promise<{ message: string; feedback_id: string }> {
    return await apiClient.post(`/interviews/sessions/${sessionId}/feedback`, data)
  },

  // Generate interview scorecard
  async generateScorecard(sessionId: string): Promise<InterviewScorecardResponse> {
    return await apiClient.get(`/interviews/sessions/${sessionId}/scorecard`)
  },

  // Schedule next interview round
  async scheduleNextRound(sessionId: string): Promise<InterviewPreparationResponse> {
    return await apiClient.post(`/interviews/sessions/${sessionId}/schedule-next`)
  },

  // Get interview analytics
  async getAnalytics(): Promise<any> {
    return await apiClient.get('/interviews/analytics')
  }
}