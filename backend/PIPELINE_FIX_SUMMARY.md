# Pipeline Stage Movement Fix Summary

## Issue
When interviews were scheduled or completed, candidates were not automatically moving to the appropriate pipeline stages:
- Scheduling interview: Candidate should move from "Screening" → "Interview"
- Completing interview with "hire" recommendation: Should move to "Offer" stage
- Completing interview with "no_hire" recommendation: Should move to "Rejected" stage

## Root Cause
The pipeline stage updates were happening in separate service calls that could fail or be rolled back, leaving the candidate in their original stage.

## Fix Applied

### 1. Interview Preparation Endpoint (`/api/v1/interviews/prepare`)
Updated to handle stage transitions directly in the same transaction:

```python
# In app/api/v1/endpoints/interviews.py, lines 130-179
if request.pipeline_state_id:
    # Get the pipeline state
    pipeline_state = await db.execute(...)
    
    if pipeline_state and pipeline_state.current_stage_id != "interview":
        # Update the stage directly in the same transaction
        pipeline_state.current_stage_id = "interview"
        pipeline_state.entered_stage_at = datetime.utcnow()
        pipeline_state.updated_at = datetime.utcnow()
        
        # Create stage change activity
        stage_activity = PipelineActivity(...)
        db.add(stage_activity)

# Single commit for everything
await db.commit()
```

### 2. Interview Update Endpoint (`/api/v1/interviews/{session_id}`)
Updated to handle stage transitions directly in the same transaction when interview is completed:

```python
# In app/api/v1/endpoints/interviews.py, lines 397-468
if session.pipeline_state_id and update_dict["status"] == InterviewStatus.COMPLETED:
    if session.overall_rating or session.recommendation:
        # Get current pipeline state
        pipeline_state = await db.execute(...)
        
        if pipeline_state and pipeline_state.current_stage_id == "interview":
            # Determine next stage based on interview outcome
            if session.recommendation == "hire" or session.overall_rating >= 4:
                next_stage = "offer"
            elif session.recommendation == "no_hire" or session.overall_rating < 2:
                next_stage = "rejected"
            
            if next_stage:
                # Update the stage directly in the same transaction
                pipeline_state.current_stage_id = next_stage
                pipeline_state.entered_stage_at = datetime.utcnow()
                
                # Create stage change activity
                stage_activity = PipelineActivity(...)
                db.add(stage_activity)

# Single commit for everything
await db.commit()
```

## Testing Instructions

### 1. Start the Backend Server
```bash
cd backend
source venv/Scripts/activate  # On Windows
# or
source venv/bin/activate      # On Linux/Mac

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test Interview Scheduling
1. Go to Pipeline Management page
2. Find a candidate in "Screening" stage
3. Click on the candidate to open details drawer
4. Click "Schedule Interview" button
5. Complete the interview preparation form
6. Verify the candidate automatically moves to "Interview" stage

### 3. Test Interview Completion
1. Complete an interview for a candidate
2. Give a rating of 4+ or recommendation of "hire"
3. Verify the candidate moves to "Offer" stage
4. Or give a rating below 2 or recommendation of "no_hire"
5. Verify the candidate moves to "Rejected" stage

### 4. Verify with Test Script
```bash
cd backend
python test_pipeline_fix.py
```

## Key Changes Made

1. **Direct Stage Updates**: Instead of calling a service method that might fail, we update the pipeline stage directly in the same database transaction as the interview creation.

2. **Proper Transaction Handling**: All updates (interview session, pipeline state, activities) happen in a single transaction with one commit at the end.

3. **Comprehensive Logging**: Added detailed logging to track stage movements and debug any issues.

4. **Error Handling**: If stage movement fails, it logs the error but doesn't fail the entire interview creation.

## Files Modified

1. `/backend/app/api/v1/endpoints/interviews.py` - Updated `prepare_interview` endpoint
2. `/backend/app/models/interview.py` - Added `pipeline_state_id` field to InterviewSession model
3. `/backend/app/services/interview_pipeline_integration.py` - Service for handling interview-pipeline integration
4. `/frontend/components/pipeline/CandidateDetailsDrawer.tsx` - Added Schedule Interview button
5. `/frontend/app/dashboard/interviews/prepare/page.tsx` - Updated to handle pipeline_state_id parameter

## Database Changes

Added `pipeline_state_id` column to `interview_sessions` table:
```sql
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS pipeline_state_id UUID REFERENCES candidate_pipeline_states(id);
```

## Monitoring

Watch the backend logs for these key messages:
- "Processing pipeline integration for pipeline_state_id: ..."
- "Moving candidate from {old_stage} to interview stage"
- "Stage updated from {old_stage} to interview"

These indicate the fix is working correctly.