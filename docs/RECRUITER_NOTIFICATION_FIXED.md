# Recruiter Notification Emails - Fixed

## Issue Fixed
The recruiter notification email was always showing "New Candidate Submission" in the subject and header, even for profile updates.

## Corrected Email Formats

### For Profile Updates

```
================================================== MOCK EMAIL ==================================================
TO: promtitude@gmail.com
SUBJECT: Profile Update - Michelle Garcia
FROM: Promtitude Team <noreply@promtitude.com>

TEXT CONTENT:
----------------------------------------------------------------------------------------------------------------
Profile Update Received

Good news! A candidate has updated their profile.

Candidate: Michelle Garcia
Type: Profile Update

The candidate's information has been automatically processed and is now available in your resume database.

View in dashboard: http://localhost:3000/dashboard/resumes
----------------------------------------------------------------------------------------------------------------
```

### For New Submissions

```
================================================== MOCK EMAIL ==================================================
TO: promtitude@gmail.com
SUBJECT: New Candidate Submission - John Doe
FROM: Promtitude Team <noreply@promtitude.com>

TEXT CONTENT:
----------------------------------------------------------------------------------------------------------------
New Candidate Submission

Good news! A candidate has submitted their information.

Candidate: John Doe
Type: New Submission

The candidate's information has been automatically processed and is now available in your resume database.

View in dashboard: http://localhost:3000/dashboard/resumes
----------------------------------------------------------------------------------------------------------------
```

## What Changed

1. **Dynamic Subject Line**:
   - Profile updates: "Profile Update - [Name]"
   - New submissions: "New Candidate Submission - [Name]"

2. **Dynamic Header**:
   - Profile updates: "Profile Update Received"
   - New submissions: "New Candidate Submission"

3. **Dynamic Message**:
   - Profile updates: "A candidate has updated their profile"
   - New submissions: "A candidate has submitted their information"

## HTML Email Features

The HTML version includes:
- Color-coded header (blue)
- Formatted candidate information box
- Clear CTA button to view resume
- Professional styling

## Implementation

The email service now checks the `submission_type` parameter:
- If `submission_type == 'update'`, it formats as a profile update
- Otherwise, it formats as a new submission

This ensures recruiters immediately know whether they're receiving a new candidate or an update to an existing profile.