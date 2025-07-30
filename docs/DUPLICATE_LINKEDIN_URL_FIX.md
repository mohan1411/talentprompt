# Fix: Duplicate LinkedIn URL Constraint Error

## Issue
When multiple candidates submit without a LinkedIn URL, the system was trying to insert empty strings `''` which violates the unique constraint on the `linkedin_url` column.

## Error Details
```
duplicate key value violates unique constraint "ix_resumes_linkedin_url"
DETAIL: Key (linkedin_url)=() already exists.
```

## Root Cause
The database has a unique index on `linkedin_url`, meaning each value must be unique. However:
- Multiple empty strings `''` violate this constraint
- NULL values are allowed and don't conflict with each other in unique constraints

## Solution
Changed the code to use `None` (NULL) instead of empty strings for LinkedIn URLs:

### Before:
```python
linkedin_url=submission.linkedin_url or "",  # Empty string causes conflict
```

### After:
```python
linkedin_url=submission.linkedin_url or None,  # NULL doesn't conflict
```

## Additional Fixes

### 1. **Location Field**
Also set location to `None` if empty to maintain consistency:
```python
location=location or None,  # Set to None if empty
```

### 2. **Update Logic**
Fixed the update logic to properly handle empty LinkedIn URLs:
```python
if submission.linkedin_url:
    resume.linkedin_url = submission.linkedin_url
elif submission.linkedin_url == "":
    resume.linkedin_url = None
```

### 3. **Transaction Rollback**
Added rollback handling to prevent cascading errors:
```python
await db.rollback()  # Rollback on error to prevent transaction issues
```

### 4. **Better Error Messages**
Improved the duplicate submission error message:
```
"This submission has already been processed. Each submission link can only be used once."
```

## Database Behavior

### With Empty Strings (FAILS):
- Resume 1: `linkedin_url = ''`
- Resume 2: `linkedin_url = ''` ❌ UNIQUE CONSTRAINT VIOLATION

### With NULL Values (WORKS):
- Resume 1: `linkedin_url = NULL`
- Resume 2: `linkedin_url = NULL` ✅ NO CONFLICT
- Resume 3: `linkedin_url = 'linkedin.com/in/johndoe'` ✅ UNIQUE VALUE

## How NULL Works in Unique Constraints

In PostgreSQL (and most databases):
- NULL values are considered distinct from each other
- Multiple NULL values don't violate unique constraints
- This allows optional fields to remain unique when provided

## Testing

1. Submit multiple profiles without LinkedIn URLs - should work
2. Submit profiles with unique LinkedIn URLs - should work
3. Try to submit with duplicate LinkedIn URLs - should fail with proper error
4. Try to use same submission link twice - should get clear error message