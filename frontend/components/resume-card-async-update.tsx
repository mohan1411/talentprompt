// Example implementation for async resume card updates

import { useState, useEffect } from 'react';
import { Resume } from '@/lib/api/client';
import { useResumePolling } from '@/hooks/useResumePolling';
import { toast } from 'sonner'; // or your preferred toast library

// 1. WebSocket approach for real-time updates
export const useResumeWebSocket = (resumes: Resume[], setResumes: (resumes: Resume[]) => void) => {
  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      // Subscribe to resume updates
      ws.send(JSON.stringify({ type: 'subscribe', channel: 'resume_updates' }));
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'resume_update') {
        const updatedResume = data.resume;
        
        // Update the resume in the list
        setResumes(prevResumes => 
          prevResumes.map(r => r.id === updatedResume.id ? updatedResume : r)
        );
        
        // Show notification
        if (data.resume.parse_status === 'completed') {
          toast.success(`Resume for ${data.resume.first_name} ${data.resume.last_name} parsed successfully`);
        } else if (data.resume.parse_status === 'failed') {
          toast.error(`Failed to parse resume for ${data.resume.first_name} ${data.resume.last_name}`);
        }
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      ws.close();
    };
  }, [setResumes]);
};

// 2. Enhanced Resume Card with loading states
export const AsyncResumeCard = ({ resume, onUpdate }: { resume: Resume; onUpdate: (resume: Resume) => void }) => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [localResume, setLocalResume] = useState(resume);
  
  // Update local state when prop changes
  useEffect(() => {
    setLocalResume(resume);
  }, [resume]);
  
  const handleRetryParsing = async () => {
    setIsUpdating(true);
    try {
      const response = await fetch(`/api/v1/resumes/${resume.id}/reparse`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const updated = await response.json();
        setLocalResume(updated);
        onUpdate(updated);
        toast.success('Resume parsing restarted');
      }
    } catch (error) {
      toast.error('Failed to retry parsing');
    } finally {
      setIsUpdating(false);
    }
  };
  
  const getStatusDisplay = () => {
    if (isUpdating) {
      return (
        <div className="flex items-center gap-2">
          <div className="animate-spin h-3 w-3 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span className="text-xs text-gray-500">Updating...</span>
        </div>
      );
    }
    
    switch (localResume.parse_status) {
      case 'processing':
        return (
          <div className="flex items-center gap-2">
            <div className="animate-pulse h-2 w-2 bg-blue-500 rounded-full" />
            <span className="text-xs text-blue-600">Processing</span>
          </div>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            ✓ Parsed
          </span>
        );
      case 'failed':
        return (
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
              Failed
            </span>
            <button
              onClick={handleRetryParsing}
              className="text-xs text-blue-600 hover:text-blue-800"
              disabled={isUpdating}
            >
              Retry
            </button>
          </div>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            {localResume.parse_status}
          </span>
        );
    }
  };
  
  return (
    <div className="resume-card">
      {/* Your existing card content */}
      <div className="mt-2">
        {getStatusDisplay()}
      </div>
    </div>
  );
};

// 3. Server-Sent Events (SSE) approach
export const useResumeSSE = (setResumes: (resumes: Resume[]) => void) => {
  useEffect(() => {
    const eventSource = new EventSource('/api/v1/resumes/updates/stream');
    
    eventSource.onmessage = (event) => {
      const updated = JSON.parse(event.data);
      
      setResumes(prevResumes => 
        prevResumes.map(r => r.id === updated.id ? updated : r)
      );
    };
    
    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
    };
    
    return () => {
      eventSource.close();
    };
  }, [setResumes]);
};