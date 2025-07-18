import { apiClient } from './client';

export interface QueueStatus {
  status_counts: {
    pending: number;
    processing: number;
    completed: number;
    failed: number;
  };
  total: number;
  is_processing: boolean;
  rate_limit_ok: boolean;
  rate_limits: {
    hourly: {
      current: number;
      limit: number;
    };
    daily: {
      current: number;
      limit: number;
    };
  };
  recent_items: Array<{
    id: string;
    status: string;
    created_at: string;
    profile_name: string;
  }>;
}

export interface ImportStats {
  daily_stats: Record<string, any>;
  source_totals: Record<string, number>;
  total_imports: number;
}

export interface QueueProfilesRequest {
  profiles: Array<Record<string, any>>;
  source?: string;
}

export const bulkImportApi = {
  // Queue management
  async addToQueue(request: QueueProfilesRequest) {
    const response = await apiClient.post('/bulk-import/queue/add', request);
    return response.data;
  },

  async getQueueStatus(): Promise<QueueStatus> {
    const response = await apiClient.get<QueueStatus>('/bulk-import/queue/status');
    return response.data;
  },

  async startQueueProcessing(maxItems?: number) {
    const params = maxItems ? { max_items: maxItems } : {};
    const response = await apiClient.post('/bulk-import/queue/process', null, { params });
    return response.data;
  },

  async clearQueue(status?: string) {
    const params = status ? { status } : {};
    const response = await apiClient.delete('/bulk-import/queue/clear', { params });
    return response.data;
  },

  // File upload
  async uploadLinkedInExport(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/bulk-import/upload/linkedin-export', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Statistics
  async getImportStats(days: number = 30): Promise<ImportStats> {
    const response = await apiClient.get<ImportStats>('/bulk-import/stats', {
      params: { days },
    });
    return response.data;
  },

  // Compliance
  async getComplianceLimits() {
    const response = await apiClient.get('/bulk-import/compliance/limits');
    return response.data;
  },
};