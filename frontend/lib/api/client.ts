/**
 * API client for Promtitude backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://talentprompt-production.up.railway.app';

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

async function makeRequest(endpoint: string, options: RequestOptions & { params?: any } = {}) {
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
  let url = `${API_BASE_URL}/api/v1${endpoint}`;
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
  }>) {
    return makeRequest('/users/me', {
      method: 'PUT',
      body: data,
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