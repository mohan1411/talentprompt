/**
 * API client for Promtitude backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
// Force production URL if on promtitude.com or any production domain
const ACTUAL_API_URL = typeof window !== 'undefined' && 
  (window.location.hostname === 'promtitude.com' || 
   window.location.hostname === 'www.promtitude.com' ||
   window.location.hostname.includes('promtitude') ||
   window.location.hostname.includes('vercel.app'))
  ? 'https://talentprompt-production.up.railway.app' 
  : API_BASE_URL;

// Debug log for API URL
if (typeof window !== 'undefined') {
  console.log('Current hostname:', window.location.hostname);
  console.log('API Base URL from env:', API_BASE_URL);
  console.log('Actual API URL being used:', ACTUAL_API_URL);
}

export class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(detail);
    this.name = 'ApiError';
  }
}

interface RequestOptions {
  method?: string;
  headers?: Record<string, string>;
  body?: any;
  formData?: FormData;
}

export async function makeRequest(endpoint: string, options: RequestOptions & { params?: any } = {}) {
  const headers: Record<string, string> = {
    ...options.headers,
  };

  // Get token from localStorage
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  
  // Add auth header if we have a token
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Add content-type for JSON requests
  if (options.body && !options.formData) {
    headers['Content-Type'] = 'application/json';
  }

  // Build URL with query params
  let url = `${ACTUAL_API_URL}/api/v1${endpoint}`;
  if (options.params) {
    const params = new URLSearchParams();
    Object.entries(options.params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    });
    const queryString = params.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }

  const config: RequestInit = {
    method: options.method || 'GET',
    headers,
    body: options.formData || (options.body ? JSON.stringify(options.body) : undefined),
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    
    // Handle different error formats from FastAPI
    let errorMessage = 'Request failed';
    
    if (typeof error.detail === 'string') {
      errorMessage = error.detail;
    } else if (Array.isArray(error.detail)) {
      // Validation errors from FastAPI
      errorMessage = error.detail.map((e: any) => e.msg || e.message || 'Validation error').join(', ');
    } else if (error.detail && typeof error.detail === 'object') {
      // Single validation error object
      errorMessage = error.detail.msg || error.detail.message || JSON.stringify(error.detail);
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    throw new ApiError(response.status, errorMessage);
  }

  return response.json();
}

// Create an axios-like API client
export const apiClient = {
  get: (url: string, options?: { params?: any; headers?: Record<string, string> }) => 
    makeRequest(url, { method: 'GET', ...options }),
  
  post: (url: string, data?: any, options?: { headers?: Record<string, string> }) => 
    makeRequest(url, { method: 'POST', body: data, ...options }),
  
  put: (url: string, data?: any, options?: { headers?: Record<string, string> }) => 
    makeRequest(url, { method: 'PUT', body: data, ...options }),
  
  patch: (url: string, data?: any, options?: { headers?: Record<string, string> }) => 
    makeRequest(url, { method: 'PATCH', body: data, ...options }),
  
  delete: (url: string, options?: { headers?: Record<string, string> }) => 
    makeRequest(url, { method: 'DELETE', ...options }),
};

// Auth endpoints
export const authApi = {
  async login(username: string, password: string) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    return makeRequest('/auth/login', {
      method: 'POST',
      formData,
    });
  },

  async register(data: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
    company?: string;
    job_title?: string;
    recaptchaToken?: string;
    marketingOptIn?: boolean;
  }) {
    return makeRequest('/auth/register', {
      method: 'POST',
      body: data,
    });
  },

  async getMe() {
    return makeRequest('/users/me');
  },

  async updateMe(data: Partial<{
    full_name: string;
    company: string;
    job_title: string;
    phone: string;
  }>) {
    return makeRequest('/users/me', {
      method: 'PUT',
      body: data,
    });
  },

  async verifyEmail(token: string) {
    return makeRequest('/auth/verify-email', {
      method: 'POST',
      params: { token },
    });
  },

  async resendVerification(email: string) {
    return makeRequest('/auth/resend-verification', {
      method: 'POST',
      params: { email },
    });
  },

  // Extension token methods
  async generateExtensionToken() {
    return makeRequest('/auth/generate-extension-token', {
      method: 'POST'
    });
  },
  
  async getExtensionTokenStatus() {
    return makeRequest('/auth/extension-token-status');
  },
  
  async revokeExtensionToken() {
    return makeRequest('/auth/revoke-extension-token', {
      method: 'DELETE'
    });
  },
};

// OAuth endpoints
export const oauthApi = {
  async initiateGoogleLogin(redirectUri?: string) {
    const params = redirectUri ? { redirect_uri: redirectUri } : {};
    return makeRequest('/auth/oauth/google/login', { params });
  },

  async initiateLinkedInLogin(redirectUri?: string) {
    const params = redirectUri ? { redirect_uri: redirectUri } : {};
    return makeRequest('/auth/oauth/linkedin/login', { params });
  },

  async handleGoogleCallback(code: string, state: string) {
    return makeRequest('/auth/oauth/google/callback', {
      params: { code, state }
    });
  },

  async handleLinkedInCallback(code: string, state: string) {
    return makeRequest('/auth/oauth/linkedin/callback', {
      params: { code, state }
    });
  },
  
  async exchangeToken(code: string, provider: 'google' | 'linkedin', redirectUri?: string) {
    return makeRequest('/auth/oauth/v2/token', {
      method: 'POST',
      body: {
        code,
        provider,
        redirect_uri: redirectUri || `${window.location.origin}/auth/${provider}/callback`
      }
    });
  },

  async linkOAuthAccount(provider: 'google' | 'linkedin', oauthData: any) {
    return makeRequest(`/auth/oauth/link/${provider}`, {
      method: 'POST',
      body: oauthData,
    });
  },

  // Mock OAuth login for testing
  async mockOAuthLogin(email: string) {
    return makeRequest('/oauth/mock/login', {
      method: 'POST',
      params: { email }
    });
  },
};

// Resume endpoints
export const resumeApi = {
  async upload(file: File, jobPosition?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (jobPosition) {
      formData.append('job_position', jobPosition);
    }

    return makeRequest('/resumes/', {
      method: 'POST',
      formData,
    });
  },

  async getMyResumes(skip = 0, limit = 100) {
    return makeRequest(`/resumes/?skip=${skip}&limit=${limit}`);
  },

  async getResume(id: string) {
    return makeRequest(`/resumes/${id}`);
  },

  async updateResume(id: string, data: any) {
    return makeRequest(`/resumes/${id}`, {
      method: 'PUT',
      body: data,
    });
  },

  async deleteResume(id: string) {
    return makeRequest(`/resumes/${id}`, {
      method: 'DELETE',
    });
  },

  async bulkDelete(resumeIds: string[]) {
    return makeRequest('/resumes/bulk/delete', {
      method: 'POST',
      body: { resume_ids: resumeIds },
    });
  },

  async bulkUpdatePosition(resumeIds: string[], jobPosition: string) {
    return makeRequest('/resumes/bulk/update-position', {
      method: 'POST',
      body: { resume_ids: resumeIds, job_position: jobPosition },
    });
  },

  async getStatistics(aggregation: 'daily' | 'weekly' | 'monthly' | 'yearly' = 'daily', startDate?: string, endDate?: string) {
    const params: any = { aggregation };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    
    return makeRequest('/resumes/statistics', { params });
  },

  async retryParsing(resumeId: string) {
    return makeRequest(`/resumes/${resumeId}/reparse`, {
      method: 'POST',
    });
  },
};

// Search endpoints
export const searchApi = {
  async searchResumes(data: {
    query: string;
    limit?: number;
    filters?: {
      location?: string;
      min_experience?: number;
      max_experience?: number;
      skills?: string[];
    };
  }) {
    return makeRequest('/search/', {
      method: 'POST',
      body: data,
    });
  },

  async getSimilarResumes(resumeId: string, limit = 5) {
    return makeRequest(`/search/similar/${resumeId}?limit=${limit}`);
  },

  async getSearchSuggestions(query: string) {
    return makeRequest(`/search/suggestions?q=${encodeURIComponent(query)}`);
  },

  async getPopularTags(limit = 30) {
    return makeRequest(`/search/popular-tags?limit=${limit}`);
  },
};

// Types
export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  company?: string;
  job_title?: string;
  phone?: string;
  created_at: string;
  updated_at?: string;
}

export interface Resume {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  location?: string;
  summary?: string;
  current_title?: string;
  years_experience?: number;
  raw_text?: string;
  parsed_data?: any;
  keywords?: string[];
  skills?: string[];
  original_filename?: string;
  file_size?: number;
  file_type?: string;
  status: string;
  parse_status: string;
  created_at: string;
  updated_at?: string;
  parsed_at?: string;
  view_count: number;
  search_appearance_count: number;
  job_position?: string;
  linkedin_url?: string;
}

export interface SearchResult {
  id: string;
  first_name: string;
  last_name: string;
  current_title?: string;
  location?: string;
  years_experience?: number;
  skills?: string[];
  score: number;
  highlights: string[];
  summary_snippet?: string;
  job_position?: string;
  linkedin_url?: string;
}

export interface SearchSuggestion {
  query: string;
  count: number;
  confidence: number;
  category: string;
}

export interface PopularTag {
  name: string;
  count: number;
  category: string;
}

// Submission API
export const submissionApi = {
  async createSubmission(data: {
    submission_type: 'update' | 'new';
    candidate_id?: string;
    candidate_email: string;
    candidate_name: string;
    message?: string;
    deadline_days?: number;
  }) {
    // Map frontend field names to backend field names
    const requestData = {
      submission_type: data.submission_type,
      candidate_id: data.candidate_id,
      email: data.candidate_email,  // backend expects 'email' not 'candidate_email'
      candidate_name: data.candidate_name,
      message: data.message,
      expires_in_days: data.deadline_days || 7,  // backend expects 'expires_in_days' not 'deadline_days'
      resume_id: data.candidate_id  // for update submissions, backend expects resume_id
    };
    
    return makeRequest('/submissions/', {
      method: 'POST',
      body: requestData,
    });
  },

  async getSubmission(token: string) {
    return makeRequest(`/submissions/${token}`, {
      headers: { 'Authorization': '' } // Public endpoint, no auth needed
    });
  },

  async submitCandidateData(token: string, data: FormData) {
    return makeRequest(`/submissions/submit/${token}`, {
      method: 'POST',
      formData: data,
      headers: { 'Authorization': '' } // Public endpoint, no auth needed
    });
  },

  async getMySubmissions(skip = 0, limit = 100) {
    return makeRequest(`/submissions/?skip=${skip}&limit=${limit}`);
  },

  async getCampaigns(skip = 0, limit = 20) {
    return makeRequest(`/submissions/campaigns?skip=${skip}&limit=${limit}`);
  },

  async getCampaignDetails(campaignId: string) {
    return makeRequest(`/submissions/campaigns/${campaignId}`);
  },
};

// Pipeline endpoints
export const pipelineApi = {
  // Pipeline CRUD
  async createPipeline(data: any) {
    return makeRequest('/workflow/', {
      method: 'POST',
      body: data,
    });
  },

  async getPipelines(teamId?: string, includeInactive?: boolean) {
    const params = new URLSearchParams();
    if (teamId) params.append('team_id', teamId);
    if (includeInactive) params.append('include_inactive', 'true');
    
    return makeRequest(`/workflow/?${params.toString()}`);
  },

  async getDefaultPipeline(teamId?: string) {
    const params = teamId ? `?team_id=${teamId}` : '';
    return makeRequest(`/workflow/default${params}`);
  },

  async getPipeline(pipelineId: string) {
    return makeRequest(`/workflow/${pipelineId}`);
  },

  async updatePipeline(pipelineId: string, data: any) {
    return makeRequest(`/workflow/${pipelineId}`, {
      method: 'PUT',
      body: data,
    });
  },

  async deletePipeline(pipelineId: string) {
    return makeRequest(`/workflow/${pipelineId}`, {
      method: 'DELETE',
    });
  },

  // Candidate pipeline management
  async addCandidateToPipeline(data: any) {
    return makeRequest('/workflow/candidates/add', {
      method: 'POST',
      body: data,
    });
  },

  async moveCandidateStage(pipelineStateId: string, data: any) {
    return makeRequest(`/workflow/candidates/${pipelineStateId}/move`, {
      method: 'PUT',
      body: data,
    });
  },

  async assignCandidate(pipelineStateId: string, assigneeId: string | null) {
    return makeRequest(`/workflow/candidates/${pipelineStateId}/assign`, {
      method: 'PUT',
      body: { assignee_id: assigneeId },
    });
  },

  async getPipelineCandidates(pipelineId: string, options?: {
    stageId?: string;
    assignedTo?: string;
    includeInactive?: boolean;
    limit?: number;
    offset?: number;
  }) {
    const params = new URLSearchParams();
    if (options?.stageId) params.append('stage_id', options.stageId);
    if (options?.assignedTo) params.append('assigned_to', options.assignedTo);
    if (options?.includeInactive) params.append('include_inactive', 'true');
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.offset) params.append('offset', options.offset.toString());
    
    return makeRequest(`/workflow/candidates/${pipelineId}?${params.toString()}`);
  },

  // Collaboration
  async addNote(candidateId: string, data: any, pipelineStateId?: string) {
    const params = pipelineStateId ? `?pipeline_state_id=${pipelineStateId}` : '';
    return makeRequest(`/workflow/candidates/${candidateId}/notes${params}`, {
      method: 'POST',
      body: data,
    });
  },

  async getNotes(candidateId: string, pipelineStateId?: string, includePrivate?: boolean) {
    const params = new URLSearchParams();
    if (pipelineStateId) params.append('pipeline_state_id', pipelineStateId);
    if (includePrivate) params.append('include_private', 'true');
    
    return makeRequest(`/workflow/candidates/${candidateId}/notes?${params.toString()}`);
  },

  async addEvaluation(candidateId: string, data: any, pipelineStateId?: string) {
    const params = pipelineStateId ? `?pipeline_state_id=${pipelineStateId}` : '';
    return makeRequest(`/workflow/candidates/${candidateId}/evaluations${params}`, {
      method: 'POST',
      body: data,
    });
  },

  async getCandidateTimeline(candidateId: string, pipelineStateId?: string) {
    const params = pipelineStateId ? `?pipeline_state_id=${pipelineStateId}` : '';
    return makeRequest(`/workflow/candidates/${candidateId}/timeline${params}`);
  },

  // Analytics
  async getPipelineAnalytics(pipelineId: string) {
    return makeRequest(`/workflow/${pipelineId}/analytics`);
  },
};

// Interview endpoints
export const interviewApi = {
  async prepareInterview(data: {
    resume_id: string;
    job_position: string;
    job_requirements?: string;
    interview_type?: string;
    interview_category?: string;
    pipeline_state_id?: string;
    focus_areas?: string[];
    difficulty_level?: number;
    num_questions?: number;
  }) {
    return makeRequest('/interviews/prepare', {
      method: 'POST',
      body: data,
    });
  },

  async scheduleInterviewFromPipeline(pipelineId: string, candidateId: string, data: any) {
    return makeRequest(`/workflow/${pipelineId}/candidates/${candidateId}/interviews`, {
      method: 'POST',
      body: data,
    });
  },

  async getInterview(interviewId: string) {
    return makeRequest(`/interviews/${interviewId}`);
  },

  async updateInterview(interviewId: string, data: any) {
    return makeRequest(`/interviews/${interviewId}`, {
      method: 'PUT',
      body: data,
    });
  },

  async completeInterview(interviewId: string, data: any) {
    return makeRequest(`/interviews/${interviewId}/complete`, {
      method: 'POST',
      body: data,
    });
  },

  async getMyInterviews(skip = 0, limit = 100) {
    return makeRequest(`/interviews/?skip=${skip}&limit=${limit}`);
  },
};