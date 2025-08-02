# Interview Flow Fix - Complete Summary

## Changes Made

### 1. Interview Preparation (Schedule → Prepare)
- **Changed behavior**: Candidates NO LONGER move to "Interview" stage when interview is scheduled/prepared
- **Button renamed**: "Schedule Interview" → "Prepare Interview" for clarity
- **Stage remains**: Candidate stays in current stage (e.g., "Screening") during preparation

### 2. Interview Start (Move to Interview Stage)
- **New behavior**: Candidates move to "Interview" stage when interview ACTUALLY STARTS
- **Trigger**: When interview status changes to `IN_PROGRESS`
- **Condition**: Only moves if candidate is in an early stage (not already in interview/offer/rejected/hired)

### 3. Interview Completion (Move to Final Stage)
- **Fixed behavior**: Candidates properly move based on interview outcome
- **Logic**:
  - Rating >= 4 OR recommendation = "hire" → Move to "Offer"
  - Rating < 2 OR recommendation = "no_hire" → Move to "Rejected"
  - Otherwise → Stay in current stage for review

## Testing the Fix

### Step 1: Restart Backend
```bash
cd backend
# Kill any existing process
pkill -f "uvicorn app.main:app"

# Start fresh
source venv/Scripts/activate  # Windows
# or
source venv/bin/activate      # Linux/Mac

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Test Interview Flow
1. Find a candidate in "Screening" stage
2. Click "Prepare Interview" - candidate should REMAIN in "Screening"
3. Go to the interview and click "Start Interview" - candidate moves to "Interview"
4. Complete the interview with rating >= 4 - candidate moves to "Offer"

### Step 3: Fix Existing Candidates
For candidates stuck in wrong stages, run the appropriate SQL script:
- `fix_ruth_johnson.sql` - For Ruth Johnson
- `fix_donna_hall.sql` - For Donna Hall
- `fix_michelle_garcia.sql` - For Michelle Garcia

## Key Code Changes

### Backend: `/app/api/v1/endpoints/interviews.py`

1. **Prepare Interview** (lines 110-128):
   - Removed automatic stage movement
   - Only creates INTERVIEW_SCHEDULED activity

2. **Update Interview** (lines 356-399):
   - Added stage movement when status = IN_PROGRESS
   - Keeps existing completion logic for moving to offer/rejected

### Frontend: `/components/pipeline/CandidateDetailsDrawer.tsx`
- Renamed button from "Schedule Interview" to "Prepare Interview" for clarity

## Monitoring

Watch backend logs for these messages:
- "Interview scheduled for candidate, but NOT moving to Interview stage yet"
- "Interview starting - checking if need to move candidate to Interview stage"
- "Moving candidate from screening to interview stage"
- "Moving candidate to offer stage - rating: X"

## Expected Flow

1. **Screening Stage** → Click "Prepare Interview" → Still in **Screening Stage**
2. **Screening Stage** → Start Interview → **Interview Stage**
3. **Interview Stage** → Complete with high rating → **Offer Stage**
4. **Interview Stage** → Complete with low rating → **Rejected Stage**