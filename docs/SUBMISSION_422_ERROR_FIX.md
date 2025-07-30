# Fixing 422 Unprocessable Entity Error on Submission

## Issue
Getting 422 error when submitting candidate profile through the public submission form.

## Root Causes Fixed

### 1. LinkedIn URL Validation
- **Problem**: Backend expected `HttpUrl` type, frontend sent plain string
- **Fix**: Changed `linkedin_url` from `HttpUrl` to `str` in schemas
- Added custom validator to handle LinkedIn URLs properly

### 2. Schema Mismatch
- **Problem**: `SubmissionSubmit` was inheriting from `SubmissionBase` which had different field types
- **Fix**: Made `SubmissionSubmit` inherit directly from `BaseModel` with all fields explicitly defined

## Updated Schema

```python
class SubmissionSubmit(BaseModel):
    """Schema for candidate submitting their information."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None  # Changed from HttpUrl
    availability: Optional[str] = None
    salary_expectations: Optional[Dict[str, Any]] = None
    location_preferences: Optional[Dict[str, Any]] = None
    resume_file: Optional[str] = None  # Base64 encoded
    resume_text: Optional[str] = None
```

## Frontend Data Format

The frontend sends data in this format:
```json
{
  "email": "test@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "availability": "immediate",
  "salary_expectations": {
    "min": 50000,
    "max": 80000,
    "currency": "USD"
  },
  "location_preferences": {
    "remote": true,
    "hybrid": false,
    "onsite": false,
    "locations": ["New York", "San Francisco"]
  },
  "resume_text": "Resume content here..."
}
```

## Testing the Fix

1. Restart the backend server to pick up schema changes
2. Try submitting the form again
3. Check backend logs for the incoming data

## Additional Debugging

Added logging to the submit endpoint:
```python
logger.info(f"Received submission data for token {token}: {data.dict()}")
```

This will show exactly what data is being received and help identify any remaining validation issues.

## Common Validation Errors

1. **Email format**: Must be valid email format
2. **Required fields**: `email`, `first_name`, `last_name` are required in frontend
3. **LinkedIn URL**: Can be empty or a valid URL/username
4. **Salary expectations**: Numbers must be integers, not strings

## Next Steps

If the error persists after these fixes:
1. Check the backend logs for the exact validation error
2. Ensure all required fields are being sent
3. Verify the token is valid and not expired