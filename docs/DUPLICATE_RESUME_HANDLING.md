# Duplicate Resume Handling

## Issue
Multiple submissions were creating duplicate resume records for the same candidate (same email address).

## Solution Implemented

### 1. **Check for Existing Resume Before Creating New**
When processing a "new" submission, the system now:
1. Checks if a resume with the same email already exists for this recruiter
2. If found, updates the existing resume instead of creating a new one
3. Only creates a new resume if no existing one is found

### 2. **Update Logic**
When an existing resume is found:
- Updates all provided fields (name, phone, LinkedIn, etc.)
- Merges new data with existing data
- Updates the `updated_at` timestamp
- Logs that an update occurred instead of creation

## Code Implementation

```python
# Check if a resume with this email already exists for this recruiter
existing_resume_query = await db.execute(
    select(Resume).where(
        and_(
            Resume.user_id == submission.recruiter_id,
            Resume.email == submission.email,
            Resume.status == "active"
        )
    )
)
existing_resume = existing_resume_query.scalar_one_or_none()

if existing_resume:
    # Update existing resume instead of creating new
    logger.info(f"Found existing resume for email {submission.email}, updating instead of creating new")
    # ... update fields ...
else:
    # Create new resume only if it doesn't exist
    # ... create new resume ...
```

## Behavior Summary

### Before Fix:
- Candidate submits with email `sunil@test.com` → Creates Resume #1
- Same candidate submits again → Creates Resume #2 (DUPLICATE!)
- Resume list shows both entries

### After Fix:
- Candidate submits with email `sunil@test.com` → Creates Resume #1
- Same candidate submits again → Updates Resume #1
- Resume list shows only one entry with latest information

## Duplicate Cleanup Script

For existing duplicates, use the cleanup script:

```bash
cd backend
python scripts/remove_duplicate_resumes.py
```

This script:
1. Finds all duplicate email/recruiter combinations
2. Keeps the most recent resume
3. Marks older duplicates as "deleted" (soft delete)

## Key Points

1. **Uniqueness is per recruiter**: Different recruiters can have resumes for the same email
2. **Email is the key**: Duplicates are identified by email address
3. **Updates preserve history**: The original creation date is preserved
4. **Soft deletes**: Old duplicates are marked as "deleted", not removed from database

## Testing

1. Submit a candidate profile
2. Submit the same email again with different information
3. Verify only one resume appears in the list
4. Verify the resume has the latest information

## Edge Cases Handled

1. **Empty emails**: Won't create duplicate null entries
2. **Case sensitivity**: Email comparison is case-sensitive (consider lowercase normalization if needed)
3. **Inactive resumes**: Only checks active resumes for duplicates
4. **Different recruiters**: Each recruiter maintains their own resume database