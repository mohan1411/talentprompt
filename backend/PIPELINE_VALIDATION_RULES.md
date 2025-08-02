# Pipeline Stage Validation Rules

## Overview
This document outlines all validation rules for moving candidates between pipeline stages. The system enforces these rules to maintain hiring process integrity while allowing flexibility for exceptional cases.

## Visual Indicators
- 🟢 **Green border**: Normal progression
- 🟡 **Yellow border**: Unusual move requiring confirmation
- 🔴 **Red border**: Extreme action strongly discouraged

## Stage Transition Matrix

### Moving TO Rejected Stage

| From Stage | Validation Level | Message | Visual |
|------------|-----------------|---------|--------|
| Applied | ✅ Normal | No confirmation needed | 🟢 |
| Screening | ✅ Normal | No confirmation needed | 🟢 |
| Interview | ✅ Normal | No confirmation needed | 🟢 |
| Offer | ⚠️ Warning | "Withdrawing offer - may have legal implications" | 🟡 |
| Hired | 🚨 Critical | "Extremely unusual - serious legal consequences" | 🔴 |

### Moving TO Withdrawn Stage

| From Stage | Validation Level | Message | Visual |
|------------|-----------------|---------|--------|
| Applied | ✅ Normal | No confirmation needed | 🟢 |
| Screening | ✅ Normal | No confirmation needed | 🟢 |
| Interview | ✅ Normal | No confirmation needed | 🟢 |
| Offer | ⚠️ Warning | "Candidate withdrawal after offer" | 🟡 |
| Hired | 🚨 Critical | "Post-hire withdrawal - very unusual" | 🔴 |

### Moving FROM Rejected Stage

| To Stage | Validation Level | Message | Visual |
|----------|-----------------|---------|--------|
| Withdrawn | ✅ Normal | Reclassification allowed | 🟢 |
| Applied/Screening | ⚠️ Warning | "Reconsidering rejected candidate" | 🟡 |
| Interview | ⚠️ Warning | "Skips normal re-evaluation" | 🟡 |
| Offer/Hired | 🚨 Critical | "Highly unusual - requires justification" | 🔴 |

### Moving FROM Withdrawn Stage

| To Stage | Validation Level | Message | Visual |
|----------|-----------------|---------|--------|
| Rejected | ✅ Normal | Reclassification allowed | 🟢 |
| Applied/Screening | ⚠️ Warning | "Re-engaging withdrawn candidate" | 🟡 |
| Interview/Offer | ⚠️ Warning | "Ensure renewed interest" | 🟡 |
| Hired | 🚨 Critical | "Only if formally re-engaged" | 🔴 |

## Standard Pipeline Transitions

### Forward Skips (Active Pipeline)

| Transition | Validation | Reason |
|------------|------------|---------|
| Applied → Screening | ✅ Normal | Standard progression |
| Applied → Interview | ⚠️ Warning | Skips screening |
| Applied → Offer | 🚨 Critical | Skips screening and interview |
| Applied → Hired | 🚨 Critical | Skips entire process |
| Screening → Interview | ✅ Normal | Standard progression |
| Screening → Offer | ⚠️ Warning | Skips interview |
| Screening → Hired | 🚨 Critical | Skips interview and offer |
| Interview → Offer | ✅ Normal | Standard progression |
| Interview → Hired | ⚠️ Warning | Skips offer negotiation |
| Offer → Hired | ✅ Normal | Standard progression |

### Backward Moves (Active Pipeline)

| Transition | Validation | Reason |
|------------|------------|---------|
| Any → Previous Stage | ⚠️ Warning | Resets candidate progress |
| Hired → Any Active | 🚨 Critical | Very unusual after hiring |
| Offer → Earlier Stage | ⚠️ Warning | May need re-evaluation |

## Automated Stage Transitions

The system automatically moves candidates based on interview outcomes:

| Interview Result | Automatic Action |
|------------------|------------------|
| Rating ≥ 4 or Recommendation = "hire" | Move to Offer stage |
| Rating ≤ 2 or Recommendation = "no_hire" | Move to Rejected stage |
| Rating between 2-4 | Stay in current stage for review |

## Implementation Details

### Frontend (PipelineBoard.tsx)
- `isUnusualMove()`: Determines if move requires yellow warning
- `isExtremeSkip()`: Determines if move requires red warning
- Visual feedback during drag operations

### Backend (pipeline/page.tsx)
- Confirmation dialogs with detailed warnings
- Reason tracking for unusual moves
- Pipeline activity logging

## Best Practices

1. **Use Rejected for**: Candidates who didn't meet requirements
2. **Use Withdrawn for**: Candidates who removed themselves
3. **Document reasons**: Always provide justification for unusual moves
4. **Consult HR/Legal**: For moves involving hired candidates
5. **Track patterns**: Monitor unusual moves for process improvement

## Compliance Notes

- All stage transitions are logged in pipeline_activities table
- Unusual moves require explicit confirmation
- Critical moves (Hired → Rejected) should trigger HR review
- Maintain audit trail for legal compliance