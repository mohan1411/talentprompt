import { useEffect, useRef, useCallback } from 'react';
import { Resume } from '@/lib/api/client';

interface UseResumePollingProps {
  resumes: Resume[];
  setResumes: (resumes: Resume[]) => void;
  resumeApi: any;
  pollingInterval?: number;
}

export const useResumePolling = ({
  resumes,
  setResumes,
  resumeApi,
  pollingInterval = 5000 // Poll every 5 seconds by default
}: UseResumePollingProps) => {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef(false);

  // Get resumes that need polling (pending or processing)
  const getResumesToPoll = useCallback(() => {
    return resumes.filter(
      resume => resume.parse_status === 'pending' || resume.parse_status === 'processing'
    );
  }, [resumes]);

  // Poll for updates
  const pollForUpdates = useCallback(async () => {
    if (isPollingRef.current) return; // Prevent concurrent polls
    
    const resumesToPoll = getResumesToPoll();
    if (resumesToPoll.length === 0) {
      // Stop polling if no resumes need updates
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    isPollingRef.current = true;
    
    try {
      // Fetch updates for specific resumes
      const updatePromises = resumesToPoll.map(async (resume) => {
        try {
          const updated = await resumeApi.getResume(resume.id);
          return updated;
        } catch (error) {
          console.error(`Failed to fetch update for resume ${resume.id}:`, error);
          return null;
        }
      });

      const updates = await Promise.all(updatePromises);
      
      // Update the resumes state with new data
      setResumes(prevResumes => {
        const updatedResumes = [...prevResumes];
        
        updates.forEach(updatedResume => {
          if (updatedResume) {
            const index = updatedResumes.findIndex(r => r.id === updatedResume.id);
            if (index !== -1) {
              // Check if status changed
              const oldStatus = updatedResumes[index].parse_status;
              const newStatus = updatedResume.parse_status;
              
              if (oldStatus !== newStatus) {
                console.log(`Resume ${updatedResume.id} status changed: ${oldStatus} → ${newStatus}`);
                
                // You can trigger notifications here
                if (newStatus === 'completed') {
                  // Show success notification
                } else if (newStatus === 'failed') {
                  // Show error notification
                }
              }
              
              updatedResumes[index] = updatedResume;
            }
          }
        });
        
        return updatedResumes;
      });
    } catch (error) {
      console.error('Polling error:', error);
    } finally {
      isPollingRef.current = false;
    }
  }, [getResumesToPoll, resumeApi, setResumes]);

  // Start polling when component mounts or when resumes change
  useEffect(() => {
    const resumesToPoll = getResumesToPoll();
    
    if (resumesToPoll.length > 0 && !intervalRef.current) {
      // Start polling
      console.log(`Starting polling for ${resumesToPoll.length} resumes`);
      pollForUpdates(); // Poll immediately
      intervalRef.current = setInterval(pollForUpdates, pollingInterval);
    } else if (resumesToPoll.length === 0 && intervalRef.current) {
      // Stop polling
      console.log('Stopping polling - no resumes to update');
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Cleanup on unmount
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [resumes, pollForUpdates, pollingInterval, getResumesToPoll]);

  // Manual refresh function
  const refreshResume = useCallback(async (resumeId: string) => {
    try {
      const updated = await resumeApi.getResume(resumeId);
      if (updated) {
        setResumes(prevResumes => 
          prevResumes.map(r => r.id === resumeId ? updated : r)
        );
      }
    } catch (error) {
      console.error(`Failed to refresh resume ${resumeId}:`, error);
    }
  }, [resumeApi, setResumes]);

  return {
    pollForUpdates,
    refreshResume,
    isPolling: intervalRef.current !== null
  };
};