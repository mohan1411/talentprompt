# How to Find the Exact Backend Error

The 500 error at resume position 95+ is happening in the backend API. To find the exact cause:

## 1. Check Backend Terminal

Look for the Python traceback in your backend terminal window. It should show something like:

```
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "...", line X, in ...
    [exact error details]
```

## 2. Common Errors and Solutions

### A. JSON Serialization Error
```
TypeError: Object of type 'X' is not JSON serializable
```
**Solution**: Some field has an unsupported data type. Check JSONB fields.

### B. Pydantic Validation Error
```
ValidationError: field required
```
**Solution**: A required field is null or missing.

### C. Database Array Error
```
ValueError: invalid literal for int() with base 10
```
**Solution**: Skills or other array field is corrupted.

### D. Memory/Size Error
```
MemoryError or very slow response
```
**Solution**: Resume has extremely large text fields.

## 3. Quick Fixes

### Option 1: Run the temporary fix script (RECOMMENDED)
```bash
cd backend
python scripts/temporary_fix_resume_95.py
```
Choose option 'a' to soft-delete problematic resumes.

### Option 2: Manually check the database
```sql
-- Find resume at position 95
WITH ordered_resumes AS (
    SELECT 
        r.*,
        row_number() OVER (ORDER BY r.created_at DESC) - 1 as position
    FROM resumes r
    JOIN users u ON r.user_id = u.id
    WHERE u.email = 'promtitude@gmail.com'
    AND r.status != 'deleted'
)
SELECT * FROM ordered_resumes WHERE position = 95;
```

### Option 3: Update frontend to handle the error gracefully
The workaround is already implemented in the frontend to only fetch the first 95 resumes.

## 4. Permanent Fix

Once you identify the exact error from the backend logs, we can implement a proper fix in the API code to handle the specific issue.