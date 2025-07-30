# Resume Update Behavior

## How Resume Updates Work

When a candidate submits their information through an update link, the system **UPDATES** the existing resume record rather than deleting and creating a new one.

## What Gets Updated

### 1. **Contact Information**
- Email address (if provided)
- Phone number (if provided)
- LinkedIn URL (if provided)
- First name (if provided)
- Last name (if provided)

### 2. **Resume Content**
- `raw_text`: Updated with new resume text/content
- Resume file: If a new file is uploaded, it replaces the old content

### 3. **Parsed Resume Data**
- Skills: Updated from newly parsed resume
- Summary: Updated from newly parsed resume
- Current title: Updated from newly parsed resume
- Years of experience: Updated from newly parsed resume
- Other parsed fields are merged with existing data

### 4. **Metadata**
- `updated_at`: Set to current timestamp
- Original creation date is preserved

## What Is Preserved

1. **Resume ID**: Same record is updated
2. **Recruiter association**: Still belongs to same recruiter
3. **Creation date**: Original submission date preserved
4. **Historical data**: Previous values are overwritten (not versioned)

## Update Process Flow

```
1. Candidate clicks update link
2. Submits new information
3. System identifies existing resume by resume_id
4. Updates fields with new values:
   - Uses new value if provided
   - Keeps old value if not provided
5. Saves updated resume to database
6. Sends notification to recruiter
```

## Example Update Scenarios

### Scenario 1: Full Update
Candidate provides all new information:
- ✅ All fields get updated with new values
- ✅ Resume content replaced
- ✅ Contact info updated

### Scenario 2: Partial Update
Candidate only updates resume file:
- ✅ Resume content updated
- ✅ Parsed data (skills, summary) updated
- ✅ Contact info remains unchanged

### Scenario 3: Contact Only Update
Candidate only updates phone/email:
- ✅ Contact fields updated
- ✅ Resume content remains unchanged
- ✅ Skills/experience unchanged

## Important Notes

1. **No Version History**: The system currently overwrites data without keeping history
2. **No Rollback**: Once updated, previous resume version is lost
3. **Merge Strategy**: For parsed data, new values override old ones
4. **File Storage**: If implementing file storage, old files should be deleted to save space

## Future Enhancements

Consider implementing:
1. **Version History**: Keep track of all resume versions
2. **Change Tracking**: Log what fields were updated
3. **Rollback**: Allow reverting to previous versions
4. **Diff View**: Show recruiters what changed
5. **Update Notifications**: Highlight which fields were updated