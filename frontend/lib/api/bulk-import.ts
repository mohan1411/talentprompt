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
    return response;
  },

  async getQueueStatus(): Promise<QueueStatus> {
    const response = await apiClient.get('/bulk-import/queue/status');
    return response as QueueStatus;
  },

  async startQueueProcessing(maxItems?: number) {
    const url = maxItems 
      ? `/bulk-import/queue/process?max_items=${maxItems}`
      : '/bulk-import/queue/process';
    const response = await apiClient.post(url, null);
    return response;
  },

  async clearQueue(status?: string) {
    const url = status 
      ? `/bulk-import/queue/clear?status=${encodeURIComponent(status)}`
      : '/bulk-import/queue/clear';
    const response = await apiClient.delete(url);
    return response;
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
    return response;
  },

  // Statistics
  async getImportStats(days: number = 30): Promise<ImportStats> {
    const response = await apiClient.get('/bulk-import/stats', {
      params: { days },
    });
    return response as ImportStats;
  },

  // Compliance
  async getComplianceLimits() {
    const response = await apiClient.get('/bulk-import/compliance/limits');
    return response;
  },
};