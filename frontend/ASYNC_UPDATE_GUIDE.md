# Async Resume Card Updates Implementation Guide

## Overview
This guide shows how to implement real-time async updates for resume cards without page refresh.

## 1. Polling Approach (Simplest)

### Step 1: Add the polling hook to your page
```tsx
// In app/dashboard/resumes/page.tsx
import { useResumePolling } from '@/hooks/useResumePolling';

// Inside your component
const { refreshResume, isPolling } = useResumePolling({
  resumes,
  setResumes,
  resumeApi,
  pollingInterval: 5000 // 5 seconds
});
```

### Step 2: Show polling indicator
```tsx
{isPolling && (
  <div className="fixed bottom-4 right-4 bg-blue-50 px-4 py-2 rounded-lg">
    <span className="animate-pulse">Checking for updates...</span>
  </div>
)}
```

## 2. WebSocket Approach (Real-time)

### Backend WebSocket endpoint already exists at:
- `/ws` - WebSocket connection endpoint
- Automatically sends updates when resume status changes

### Frontend implementation:
```tsx
useEffect(() => {
  const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'resume_update') {
      setResumes(prev => 
        prev.map(r => r.id === data.resume.id ? data.resume : r)
      );
    }
  };
  
  return () => ws.close();
}, []);
```

## 3. Optimistic Updates

### For better UX, update UI immediately:
```tsx
const retryParsing = async (resumeId: string) => {
  // Update UI immediately
  setResumes(prev => 
    prev.map(r => 
      r.id === resumeId 
        ? { ...r, parse_status: 'processing' } 
        : r
    )
  );
  
  try {
    await resumeApi.retryParsing(resumeId);
  } catch (error) {
    // Revert on error
    setResumes(prev => 
      prev.map(r => 
        r.id === resumeId 
          ? { ...r, parse_status: 'failed' } 
          : r
      )
    );
  }
};
```

## 4. Visual Feedback

### Add loading states to cards:
```tsx
{resume.parse_status === 'processing' && (
  <div className="absolute inset-0 bg-white/50 flex items-center justify-center">
    <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
  </div>
)}
```

### Add status badges with animations:
```tsx
{resume.parse_status === 'processing' && (
  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-800">
    <span className="animate-pulse">●</span> Processing
  </span>
)}
```

## 5. Error Handling

### Show retry options for failed resumes:
```tsx
{resume.parse_status === 'failed' && (
  <button
    onClick={() => retryParsing(resume.id)}
    className="text-xs text-blue-600 hover:text-blue-800"
  >
    Retry parsing
  </button>
)}
```

## 6. Notifications

### Add toast notifications for status changes:
```tsx
// In your polling hook
if (oldStatus !== newStatus) {
  if (newStatus === 'completed') {
    toast.success(`Resume for ${resume.first_name} ${resume.last_name} parsed successfully`);
  } else if (newStatus === 'failed') {
    toast.error(`Failed to parse resume for ${resume.first_name} ${resume.last_name}`);
  }
}
```

## Complete Example

Here's a minimal implementation:

```tsx
// 1. Add to your resumes page
const [resumes, setResumes] = useState<Resume[]>([]);

// 2. Add polling
useEffect(() => {
  const interval = setInterval(async () => {
    const pendingResumes = resumes.filter(r => 
      r.parse_status === 'pending' || r.parse_status === 'processing'
    );
    
    if (pendingResumes.length > 0) {
      const updated = await resumeApi.getMyResumes();
      setResumes(updated);
    }
  }, 5000);
  
  return () => clearInterval(interval);
}, [resumes]);

// 3. Update resume cards to show status
<div className="mt-2">
  {resume.parse_status !== 'completed' && (
    <span className={`text-xs px-2 py-1 rounded-full ${
      resume.parse_status === 'processing' ? 'bg-blue-100 text-blue-800' :
      resume.parse_status === 'failed' ? 'bg-red-100 text-red-800' :
      'bg-gray-100 text-gray-800'
    }`}>
      {resume.parse_status}
    </span>
  )}
</div>
```

## Performance Considerations

1. **Only poll when needed** - Stop polling when no resumes are processing
2. **Batch updates** - Update multiple resumes in one state update
3. **Use React.memo** - Prevent unnecessary re-renders of unchanged cards
4. **Virtualization** - For large lists, use react-window or similar

## Testing

1. Upload a resume and watch it update from "pending" → "processing" → "completed"
2. Simulate failures by uploading invalid files
3. Test retry functionality
4. Check performance with many resumes