import { apiClient } from './client';

export interface OutreachMessageRequest {
  resume_id: string;
  job_title: string;
  company_name?: string;
  job_requirements?: {
    skills?: string[];
    min_years_experience?: number;
    nice_to_have?: string[];
    location?: string;
  };
  custom_instructions?: string;
}

export interface OutreachMessage {
  subject: string;
  body: string;
  quality_score: number;
}

export interface OutreachMessageResponse {
  success: boolean;
  messages: {
    casual: OutreachMessage;
    professional: OutreachMessage;
    technical: OutreachMessage;
  };
  candidate_name: string;
  candidate_title: string;
}

export interface MessagePerformanceTrack {
  message_id: string;
  event: 'sent' | 'opened' | 'responded' | 'not_interested';
  metadata?: Record<string, any>;
}

export interface OutreachAnalytics {
  total_messages: number;
  messages_sent: number;
  messages_opened: number;
  messages_responded: number;
  overall_response_rate: number;
  avg_response_time_hours?: number;
  best_performing_style?: string;
  best_performing_time?: string;
  by_style: Record<string, {
    total: number;
    responded: number;
    response_rate: number;
  }>;
}

export const outreachApi = {
  async generateMessages(data: OutreachMessageRequest): Promise<OutreachMessageResponse> {
    console.log('Sending outreach request:', data);
    const response = await apiClient.post('/outreach/generate', data);
    console.log('Outreach response:', response);
    return response; // The response is already the data, not wrapped in { data: ... }
  },

  async trackPerformance(data: MessagePerformanceTrack): Promise<{ success: boolean }> {
    const response = await apiClient.post('/outreach/track', data);
    return response;
  },

  async getAnalytics(days: number = 30): Promise<OutreachAnalytics> {
    const response = await apiClient.get('/outreach/analytics', {
      params: { days }
    });
    return response;
  },
};