# Candidate Submission Without Resume

## Issue Fixed
Candidates submitting their profile without uploading a resume were not appearing in the resume database.

## Root Cause
The system was creating resume records with `null` or missing values for certain fields when no resume was uploaded, which could cause issues with display or database constraints.

## Solution Implemented

### 1. **Default Values for Empty Fields**
When no resume is uploaded:
- `raw_text`: Set to empty string `""` instead of `null`
- `phone`: Set to empty string `""` if not provided
- `linkedin_url`: Set to empty string `""` if not provided
- `parse_status`: Set to `"completed"` (since there's nothing to parse)

### 2. **Validation Requirements**
The following fields are now required:
- **Email**: Must be provided
- **First Name**: Must be provided
- **Last Name**: Must be provided

### 3. **Optional Resume Upload**
- Resume upload is now truly optional
- Candidates can submit just their contact information
- Profile will still be created and visible in the resume database

## How It Works

### With Resume Upload
```json
{
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "resume_text": "Full resume content...",
  // Resume gets parsed, skills extracted, etc.
}
```

### Without Resume Upload
```json
{
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "123-456-7890",
  "linkedin_url": "linkedin.com/in/johndoe"
  // No resume content - profile still created
}
```

## Database Record Created

When no resume is uploaded, the system creates a resume record with:
- Basic contact information (name, email, phone)
- Empty resume text (`raw_text = ""`)
- Empty skills array (`skills = []`)
- Empty summary (`summary = ""`)
- `parse_status = "completed"` (nothing to parse)
- `source = "candidate_submission"`

## Benefits

1. **Flexibility**: Candidates can submit profiles without having a resume ready
2. **Quick Registration**: Allows faster candidate capture
3. **Progressive Profiling**: Candidates can add resume later through update links
4. **Contact Database**: Build a database of interested candidates even without full resumes

## Use Cases

1. **Quick Interest Registration**: Candidates can quickly express interest
2. **Mobile Submissions**: Easier to submit from mobile without file handling
3. **Network Building**: Collect contacts at events without requiring resumes
4. **Future Opportunities**: Build talent pool for future positions

## Frontend Behavior

The submission form should:
- Mark resume upload as optional (not required)
- Still require email, first name, and last name
- Allow submission without any resume content
- Show success message even without resume

## Recruiter View

In the resume list, profiles without resumes will show:
- Candidate name and contact info
- "No resume uploaded" or similar indicator
- Option to request resume through update link
- All other submission details (date, preferences, etc.)