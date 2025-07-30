# Where to Check Timestamps

## In the UI (After Fix)

The resume cards now show:
- **Uploaded**: Original creation date
- **Updated**: Last modification date (only shown if different from creation date)

### Visual Indicators

1. **New Resume Created**:
   ```
   📅 Uploaded 7/30/2025
   ```

2. **Existing Resume Updated**:
   ```
   📅 Uploaded 7/28/2025
   🔄 Updated 7/30/2025  (shown in blue)
   ```

The updated timestamp will appear in blue with a refresh icon when a resume has been modified after its initial creation.

## In the Database

If you want to check directly in the database:

```sql
-- Check specific resume by email
SELECT 
    id,
    first_name,
    last_name,
    email,
    created_at,
    updated_at,
    CASE 
        WHEN updated_at > created_at THEN 'Updated'
        ELSE 'Not Updated'
    END as status
FROM resumes
WHERE email = 'sunil@test.com'
AND status = 'active'
ORDER BY created_at DESC;

-- See all resumes with update status
SELECT 
    email,
    COUNT(*) as count,
    MAX(created_at) as latest_created,
    MAX(updated_at) as latest_updated
FROM resumes
WHERE status = 'active'
GROUP BY email
ORDER BY latest_updated DESC;
```

## In Backend Logs

When a duplicate submission updates an existing resume, you'll see:
```
INFO: Found existing resume for email sunil@test.com, updating instead of creating new
INFO: Existing resume ID: [uuid], Name: Sunil Narasimhappa
```

## How to Test

1. **Note the current state**: Check if the resume shows an "Updated" date
2. **Create a new submission link** for the same email
3. **Submit the profile** (you can change some details)
4. **Refresh the resume page**
5. **Look for the blue "Updated" timestamp**

## Expected Behavior

### First Submission
- Creates new resume
- Shows only "Uploaded" date
- Both created_at and updated_at are the same

### Subsequent Submissions (Same Email)
- Updates existing resume
- Shows both "Uploaded" and "Updated" dates
- updated_at is newer than created_at

## Quick Database Check

If you have database access:
```sql
-- Quick check for Sunil's resume
SELECT created_at, updated_at 
FROM resumes 
WHERE email = 'sunil@test.com' 
AND status = 'active';
```

If `updated_at` is newer than `created_at`, the resume was successfully updated instead of duplicated.