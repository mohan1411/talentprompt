'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Upload, FileText, Users, Clock, AlertCircle, 
  CheckCircle, XCircle, Play, Pause, Trash2,
  Download, Linkedin, Zap
} from 'lucide-react';
import { bulkImportApi } from '@/lib/api/bulk-import';
import type { QueueStatus, ImportStats } from '@/lib/api/bulk-import';

type TabType = 'queue' | 'upload' | 'webhook';

export default function BulkImportPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('queue');
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null);
  const [importStats, setImportStats] = useState<ImportStats | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  // Load queue status on mount
  useEffect(() => {
    loadQueueStatus();
    loadImportStats();

    // Set up auto-refresh when processing
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, []);

  // Auto-refresh when processing
  useEffect(() => {
    if (queueStatus?.is_processing) {
      const interval = setInterval(loadQueueStatus, 2000);
      setRefreshInterval(interval);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [queueStatus?.is_processing]);

  const loadQueueStatus = async () => {
    try {
      const status = await bulkImportApi.getQueueStatus();
      setQueueStatus(status);
      setIsProcessing(status.is_processing);
    } catch (error) {
      console.error('Failed to load queue status:', error);
    }
  };

  const loadImportStats = async () => {
    try {
      const stats = await bulkImportApi.getImportStats(30);
      setImportStats(stats);
    } catch (error) {
      console.error('Failed to load import stats:', error);
    }
  };

  const handleStartProcessing = async () => {
    try {
      setIsProcessing(true);
      await bulkImportApi.startQueueProcessing();
      await loadQueueStatus();
    } catch (error) {
      console.error('Failed to start processing:', error);
      setIsProcessing(false);
    }
  };

  const handleClearQueue = async (status?: string) => {
    if (!confirm(`Are you sure you want to clear ${status || 'all'} queue items?`)) {
      return;
    }

    try {
      await bulkImportApi.clearQueue(status);
      await loadQueueStatus();
    } catch (error) {
      console.error('Failed to clear queue:', error);
    }
  };

  const handleFileUpload = async () => {
    if (!uploadFile) return;

    setIsUploading(true);
    try {
      const result = await bulkImportApi.uploadLinkedInExport(uploadFile);
      
      // Show success message
      alert(`Successfully queued ${result.result.added} profiles for import!`);
      
      // Reset file and reload queue
      setUploadFile(null);
      await loadQueueStatus();
      
      // Switch to queue tab
      setActiveTab('queue');
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload file. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const renderQueueTab = () => {
    if (!queueStatus) return <div>Loading...</div>;

    const { status_counts, rate_limits, recent_items } = queueStatus;

    return (
      <div className="space-y-6">
        {/* Queue Summary */}
        <div className="grid grid-cols-4 gap-4">
          <div className="card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Pending</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {status_counts.pending}
                </p>
              </div>
              <Clock className="h-8 w-8 text-gray-400" />
            </div>
          </div>

          <div className="card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Processing</p>
                <p className="text-2xl font-bold text-blue-600">
                  {status_counts.processing}
                </p>
              </div>
              <div className="h-8 w-8 flex items-center justify-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              </div>
            </div>
          </div>

          <div className="card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Completed</p>
                <p className="text-2xl font-bold text-green-600">
                  {status_counts.completed}
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </div>

          <div className="card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Failed</p>
                <p className="text-2xl font-bold text-red-600">
                  {status_counts.failed}
                </p>
              </div>
              <XCircle className="h-8 w-8 text-red-600" />
            </div>
          </div>
        </div>

        {/* Rate Limits */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Rate Limits
          </h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Hourly Limit
                </span>
                <span className="text-sm font-medium">
                  {rate_limits.hourly.current} / {rate_limits.hourly.limit}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ 
                    width: `${(rate_limits.hourly.current / rate_limits.hourly.limit) * 100}%` 
                  }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Daily Limit
                </span>
                <span className="text-sm font-medium">
                  {rate_limits.daily.current} / {rate_limits.daily.limit}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ 
                    width: `${(rate_limits.daily.current / rate_limits.daily.limit) * 100}%` 
                  }}
                ></div>
              </div>
            </div>
          </div>

          {!queueStatus.rate_limit_ok && (
            <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-yellow-600 mr-2" />
                <p className="text-sm text-yellow-800 dark:text-yellow-300">
                  Rate limit reached. Please wait before importing more profiles.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Queue Actions */}
        <div className="flex gap-4">
          <button
            onClick={handleStartProcessing}
            disabled={isProcessing || status_counts.pending === 0 || !queueStatus.rate_limit_ok}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            {isProcessing ? (
              <>
                <Pause className="h-4 w-4" />
                Processing...
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Start Import
              </>
            )}
          </button>

          {status_counts.failed > 0 && (
            <button
              onClick={() => handleClearQueue('failed')}
              className="btn-secondary flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Clear Failed
            </button>
          )}

          {status_counts.pending > 0 && (
            <button
              onClick={() => handleClearQueue('pending')}
              className="btn-secondary flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Clear Pending
            </button>
          )}
        </div>

        {/* Recent Items */}
        {recent_items.length > 0 && (
          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Recent Queue Items
            </h3>
            <div className="space-y-2">
              {recent_items.map((item) => (
                <div key={item.id} className="flex items-center justify-between py-2">
                  <div>
                    <p className="font-medium">{item.profile_name}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(item.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span className={`badge ${
                    item.status === 'completed' ? 'bg-green-100 text-green-800' :
                    item.status === 'failed' ? 'bg-red-100 text-red-800' :
                    item.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {item.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderUploadTab = () => (
    <div className="max-w-2xl mx-auto">
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Upload LinkedIn Export
        </h3>
        
        <div className="space-y-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-300">
              Supported formats: LinkedIn Data Export (ZIP), Recruiter Export (CSV/Excel)
            </p>
          </div>

          <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".csv,.xlsx,.xls,.zip"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
            />
            
            <label htmlFor="file-upload" className="cursor-pointer">
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                Click to upload or drag and drop
              </p>
              <p className="text-xs text-gray-500 mt-1">
                CSV, Excel, or ZIP up to 50MB
              </p>
            </label>
          </div>

          {uploadFile && (
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center">
                <FileText className="h-5 w-5 text-gray-400 mr-2" />
                <span className="text-sm">{uploadFile.name}</span>
              </div>
              <button
                onClick={() => setUploadFile(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          <button
            onClick={handleFileUpload}
            disabled={!uploadFile || isUploading}
            className="btn-primary w-full disabled:opacity-50"
          >
            {isUploading ? 'Uploading...' : 'Upload and Queue'}
          </button>
        </div>

        <div className="mt-6 space-y-3">
          <h4 className="font-medium text-gray-900 dark:text-white">
            How to export from LinkedIn:
          </h4>
          <ol className="list-decimal list-inside space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <li>Go to LinkedIn Settings & Privacy</li>
            <li>Click "Get a copy of your data"</li>
            <li>Select "The works" and request archive</li>
            <li>Download the ZIP file when ready</li>
            <li>Upload it here</li>
          </ol>
        </div>
      </div>
    </div>
  );

  const renderWebhookTab = () => (
    <div className="max-w-2xl mx-auto">
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Third-Party Integrations
        </h3>

        <div className="space-y-6">
          <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              Your webhook URL:
            </p>
            <code className="block p-2 bg-gray-900 text-green-400 rounded text-xs">
              {`${process.env.NEXT_PUBLIC_API_URL}/api/v1/bulk-import/webhook/linkedin`}
            </code>
          </div>

          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="font-medium flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Zapier Integration
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Connect LinkedIn to Promtitude via Zapier webhooks
              </p>
            </div>

            <div className="border-l-4 border-purple-500 pl-4">
              <h4 className="font-medium flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Make.com (Integromat)
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Automate LinkedIn profile imports with Make scenarios
              </p>
            </div>

            <div className="border-l-4 border-orange-500 pl-4">
              <h4 className="font-medium flex items-center gap-2">
                <Linkedin className="h-5 w-5" />
                LinkedIn Talent Hub
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Official LinkedIn API integration (requires Talent Hub subscription)
              </p>
            </div>
          </div>

          <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
            <div className="flex items-start">
              <AlertCircle className="h-5 w-5 text-yellow-600 mr-2 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-yellow-800 dark:text-yellow-300">
                <p className="font-medium">Compliance Notice</p>
                <p className="mt-1">
                  All integrations must comply with LinkedIn's Terms of Service. 
                  Only use official APIs or approved third-party tools.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Bulk Import
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Import multiple LinkedIn profiles efficiently and compliantly
        </p>
      </div>

      {/* Chrome Extension Notice */}
      <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <div className="flex items-start">
          <Linkedin className="h-5 w-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-blue-800 dark:text-blue-300">
              LinkedIn Chrome Extension
            </p>
            <p className="mt-1 text-blue-700 dark:text-blue-400">
              Install our Chrome extension to queue profiles directly from LinkedIn search results.
            </p>
            <a 
              href="#" 
              className="inline-flex items-center mt-2 text-blue-600 hover:text-blue-700"
            >
              Install Extension
              <Download className="h-4 w-4 ml-1" />
            </a>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 mb-6 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setActiveTab('queue')}
          className={`px-4 py-2 -mb-px font-medium text-sm ${
            activeTab === 'queue'
              ? 'text-primary border-b-2 border-primary'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
          }`}
        >
          Import Queue
        </button>
        <button
          onClick={() => setActiveTab('upload')}
          className={`px-4 py-2 -mb-px font-medium text-sm ${
            activeTab === 'upload'
              ? 'text-primary border-b-2 border-primary'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
          }`}
        >
          File Upload
        </button>
        <button
          onClick={() => setActiveTab('webhook')}
          className={`px-4 py-2 -mb-px font-medium text-sm ${
            activeTab === 'webhook'
              ? 'text-primary border-b-2 border-primary'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
          }`}
        >
          Integrations
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'queue' && renderQueueTab()}
      {activeTab === 'upload' && renderUploadTab()}
      {activeTab === 'webhook' && renderWebhookTab()}

      {/* Import Stats */}
      {importStats && (
        <div className="mt-8 card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Import Statistics (Last 30 Days)
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Imports</p>
              <p className="text-2xl font-bold">{importStats.total_imports}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Sources</p>
              <div className="mt-1">
                {Object.entries(importStats.source_totals).map(([source, count]) => (
                  <div key={source} className="text-sm">
                    <span className="capitalize">{source.replace('_', ' ')}</span>: {count}
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Daily Average</p>
              <p className="text-2xl font-bold">
                {Math.round(importStats.total_imports / 30)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}