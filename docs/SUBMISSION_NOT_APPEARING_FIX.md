# Fix: Submissions Not Appearing in Resume Page

## Issues Found and Fixed

### 1. **Missing Status Field**
- **Problem**: Resume status was not explicitly set when creating from submission
- **Fix**: Added `status="active"` to ensure resumes appear in list
- **Why it matters**: The resume list query filters out non-active resumes

### 2. **Missing Location Field**
- **Problem**: Location field was not being populated
- **Fix**: Extract location from location_preferences submitted by candidate
- **Implementation**: Joins the locations array into a comma-separated string

### 3. **Better Error Handling**
- **Added**: More detailed error logging to help debug issues
- **Re-raises**: Exceptions to see actual database errors

## Complete Fix Applied

```python
# Create new resume
# Extract location from location preferences if available
location = ""
if submission.location_preferences:
    locations = submission.location_preferences.get("locations", [])
    if locations:
        location = ", ".join(locations)

resume = Resume(
    user_id=submission.recruiter_id,
    first_name=submission.first_name,
    last_name=submission.last_name,
    email=submission.email,
    phone=submission.phone or "",
    location=location,  # Add location field
    linkedin_url=submission.linkedin_url or "",
    parsed_data=submission.parsed_data or {},
    raw_text=submission.resume_text or "",  # Empty string if no resume
    source="candidate_submission",
    skills=submission.parsed_data.get("skills", []) if submission.parsed_data else [],
    current_title=submission.parsed_data.get("current_title", "") if submission.parsed_data else "",
    summary=submission.parsed_data.get("summary", "") if submission.parsed_data else "",
    years_experience=submission.parsed_data.get("years_experience", 0) if submission.parsed_data else 0,
    # Set parse status to completed since there's nothing to parse if no resume
    parse_status="completed" if not submission.resume_text else "pending",
    # Explicitly set status to active
    status="active"
)
```

## Why Resumes Were Not Appearing

The resume listing endpoint filters resumes:
```python
.where(Resume.status != 'deleted')  # Only shows non-deleted resumes
```

Without explicitly setting `status="active"`, the default might not be applied correctly, causing resumes to be filtered out.

## Testing Steps

1. **Restart backend** to pick up the changes
2. **Submit a new profile** without resume
3. **Check backend logs** for any errors
4. **Refresh resume page** - the profile should now appear

## What Should Appear

Even without a resume file, the listing should show:
- Candidate name
- Email
- Phone (if provided)
- Location (if provided)
- LinkedIn URL (if provided)
- Status: Active
- Parse Status: Completed
- Source: candidate_submission

## If Still Not Appearing

Check:
1. **Database logs** for any constraint violations
2. **Backend console** for error messages
3. **Network tab** to ensure API is returning the resume
4. **Browser console** for any frontend errors