# Complete Fix for Pipeline Stage Movement Issue

## The Real Problem

The issue is that the interview flow is split into two separate processes:

1. **Interview Session** - Conducts interview and marks it COMPLETED
2. **Scorecard Page** - Calculates rating/recommendation but doesn't save them

When the interview is marked COMPLETED, there's no `overall_rating` or `recommendation` yet, so the pipeline logic can't determine where to move the candidate.

## Solution Options

### Option 1: Save Rating When Interview Completes (Recommended)
Update the interview completion to calculate and save the rating/recommendation based on question ratings.

### Option 2: Update Pipeline After Scorecard Generation
Add an endpoint to update the interview with rating/recommendation when scorecard is viewed.

### Option 3: Move Pipeline Stage Based on Interview Status Only
Simplify the logic to move candidates based on interview completion status alone.

## Implementing Option 1 (Recommended)

We'll update the interview completion endpoint to:
1. Calculate the average rating from all rated questions
2. Determine recommendation based on the average rating
3. Save these values with the interview
4. Then the existing pipeline logic will work correctly

Here's the implementation plan:

1. Update the interview completion endpoint to calculate and save rating/recommendation
2. Ensure the pipeline logic runs AFTER these values are saved
3. Test the complete flow

This ensures the pipeline movement happens correctly when the interview is completed.