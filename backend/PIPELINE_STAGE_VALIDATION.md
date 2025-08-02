# Pipeline Stage Transition Validation

## Overview
We've implemented a stage transition validation system that maintains hiring process integrity while allowing flexibility for exceptional cases.

## How It Works

### 1. Visual Indicators While Dragging
- **Green border**: Normal progression (e.g., Screening → Interview)
- **Yellow border**: Unusual move requiring confirmation (e.g., Screening → Offer)

### 2. Confirmation Dialogs
When attempting unusual moves, users see warnings:
- **Screening → Offer**: "This will skip the interview process"
- **Moving backwards**: "This will reset their progress"
- **Applied → Interview/Offer**: "This skips the screening process"

### 3. Allowed Transitions

#### Always Allowed (No Warning):
- Adjacent stage moves (Applied → Screening → Interview → Offer → Hired)
- Any stage → Rejected (can reject at any time)
- Any stage → Withdrawn

#### Requires Confirmation:
- Screening → Offer (skips interview)
- Applied → Interview/Offer (skips screening)
- Moving backwards (e.g., Offer → Interview)

## Implementation Details

### Frontend Validation
```typescript
// Stage order definition
const stageOrder = {
  'applied': 1,
  'screening': 2,
  'interview': 3,
  'offer': 4,
  'hired': 5,
  'rejected': 0,  // Special case
  'withdrawn': 0  // Special case
};

// Check if move is unusual
if (fromStage === 'screening' && toStage === 'offer') {
  showWarning("Skipping interview process");
}
```

### Visual Feedback
- Drop zones change color based on drag source
- Yellow indicates unusual moves
- Green indicates normal progression
- Smooth transitions for better UX

## Benefits

1. **Process Integrity**: Prevents accidental stage skipping
2. **Flexibility**: Still allows overrides for exceptional cases
3. **Transparency**: Clear visual indicators and warnings
4. **Audit Trail**: Unusual moves are logged with reasons

## Future Enhancements

1. **Role-based permissions**: Different rules for managers vs recruiters
2. **Custom validation rules**: Per-pipeline stage requirements
3. **Reporting**: Track how often stages are skipped
4. **Automation rules**: Auto-reject if stuck in stage too long

## User Guide

1. **Normal flow**: Drag candidates between adjacent stages freely
2. **Skip stages**: You'll see a yellow highlight and confirmation dialog
3. **Emergency overrides**: Confirm the dialog to proceed with unusual moves
4. **Best practice**: Let the system handle stage transitions through interviews

This system balances automation with human judgment, ensuring consistent hiring practices while maintaining flexibility for edge cases.