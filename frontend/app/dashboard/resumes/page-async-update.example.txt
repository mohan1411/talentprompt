// Integration example for the resumes page
// Add this to your existing /app/dashboard/resumes/page.tsx

import { useResumePolling } from '@/hooks/useResumePolling';
import { toast } from 'sonner';

// Inside your ResumesPage component, add this after the useState declarations:

// 1. Add polling hook
const { refreshResume, isPolling } = useResumePolling({
  resumes,
  setResumes,
  resumeApi,
  pollingInterval: 5000 // Check every 5 seconds
});

// 2. Add optimistic updates
const updateResumeOptimistically = (resumeId: string, updates: Partial<Resume>) => {
  // Update UI immediately
  setResumes(prevResumes => 
    prevResumes.map(r => 
      r.id === resumeId ? { ...r, ...updates } : r
    )
  );
};

// 3. Enhanced delete with optimistic update
const handleDeleteWithOptimisticUpdate = async (resumeId: string) => {
  if (!confirm('Are you sure you want to delete this resume?')) return;
  
  // Optimistically remove from UI
  const deletedResume = resumes.find(r => r.id === resumeId);
  setResumes(resumes.filter(r => r.id !== resumeId));
  
  try {
    await resumeApi.deleteResume(resumeId);
    toast.success('Resume deleted successfully');
  } catch (error) {
    // Revert on error
    if (deletedResume) {
      setResumes(prev => [...prev, deletedResume]);
    }
    toast.error('Failed to delete resume');
  }
};

// 4. Add retry parsing function
const retryParsing = async (resumeId: string) => {
  // Update UI to show processing
  updateResumeOptimistically(resumeId, { parse_status: 'processing' });
  
  try {
    const response = await fetch(`/api/v1/resumes/${resumeId}/reparse`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      toast.success('Resume parsing restarted');
      // Polling will pick up the updates
    } else {
      throw new Error('Failed to retry');
    }
  } catch (error) {
    // Revert status on error
    updateResumeOptimistically(resumeId, { parse_status: 'failed' });
    toast.error('Failed to retry parsing');
  }
};

// 5. Add visual indicator when polling is active
{isPolling && (
  <div className="fixed bottom-4 right-4 flex items-center gap-2 bg-blue-50 text-blue-700 px-4 py-2 rounded-lg shadow-lg">
    <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
    <span className="text-sm">Checking for updates...</span>
  </div>
)}

// 6. Enhanced resume card with real-time status
const ResumeCardEnhanced = ({ resume }: { resume: Resume }) => {
  const [showActions, setShowActions] = useState(false);
  const isProcessing = resume.parse_status === 'processing';
  const isPending = resume.parse_status === 'pending';
  const isFailed = resume.parse_status === 'failed';
  
  return (
    <div className="resume-card relative">
      {/* Processing overlay */}
      {isProcessing && (
        <div className="absolute inset-0 bg-white/50 dark:bg-gray-800/50 flex items-center justify-center rounded-xl z-10">
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin h-8 w-8 border-3 border-blue-500 border-t-transparent rounded-full" />
            <span className="text-sm text-gray-600 dark:text-gray-400">Processing...</span>
          </div>
        </div>
      )}
      
      {/* Status badge with animations */}
      <div className="mt-2 flex items-center gap-2">
        {isProcessing && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
            <span className="animate-pulse">●</span> Processing
          </span>
        )}
        
        {isPending && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
            Pending
          </span>
        )}
        
        {isFailed && (
          <>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
              Failed
            </span>
            <button
              onClick={() => retryParsing(resume.id)}
              className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
            >
              Retry
            </button>
          </>
        )}
        
        {resume.parse_status === 'completed' && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
            ✓ Parsed
          </span>
        )}
      </div>
      
      {/* Rest of your card content */}
    </div>
  );
};