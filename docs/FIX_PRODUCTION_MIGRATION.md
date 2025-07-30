# Fix Production Migration - Candidate Submissions

## Error
```
relation "candidate_submissions" does not exist
```

## Quick Fix Options

### Option 1: Run Alembic Migration (Recommended)

#### Via Railway CLI:
```bash
railway run -s your-backend-service alembic upgrade head
```

#### Via Railway Dashboard:
1. Go to your Railway project
2. Click on your backend service
3. Go to "Deploy" tab
4. Click "Run Command"
5. Enter: `alembic upgrade head`
6. Click "Run"

### Option 2: Manual Table Creation

If Alembic fails, use the manual script:

#### Via Railway:
```bash
railway run -s your-backend-service python scripts/create_submission_tables.py
```

#### Or directly with DATABASE_URL:
```bash
export DATABASE_URL="your-production-database-url"
cd backend
python scripts/create_submission_tables.py
```

### Option 3: Direct SQL

Connect to your production database and run:

```sql
-- Create enums
CREATE TYPE submissiontype AS ENUM ('update', 'new');
CREATE TYPE submissionstatus AS ENUM ('pending', 'submitted', 'processed', 'expired', 'cancelled');

-- Create tables
CREATE TABLE invitation_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_type VARCHAR(50),
    source_data JSONB,
    is_public BOOLEAN DEFAULT FALSE,
    public_slug VARCHAR(100),
    email_template TEXT,
    expires_in_days INTEGER DEFAULT 7,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE candidate_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(255) UNIQUE NOT NULL,
    submission_type VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    recruiter_id UUID NOT NULL REFERENCES users(id),
    campaign_id UUID REFERENCES invitation_campaigns(id),
    resume_id UUID REFERENCES resumes(id),
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    linkedin_url VARCHAR(255),
    availability VARCHAR(50),
    salary_expectations JSONB,
    location_preferences JSONB,
    resume_text TEXT,
    parsed_data JSONB,
    email_sent_at TIMESTAMP,
    email_opened_at TIMESTAMP,
    link_clicked_at TIMESTAMP,
    submitted_at TIMESTAMP,
    processed_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX ix_candidate_submissions_token ON candidate_submissions(token);
CREATE INDEX ix_candidate_submissions_recruiter_id ON candidate_submissions(recruiter_id);
CREATE INDEX ix_candidate_submissions_email ON candidate_submissions(email);
```

## Verify Tables Were Created

After running any of the above options, verify:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN ('candidate_submissions', 'invitation_campaigns');
```

Should return:
- candidate_submissions
- invitation_campaigns

## Common Issues

1. **"type already exists" error**
   - This is OK, the types were already created
   - Tables should still be created

2. **Permission denied**
   - Make sure you're using the correct database credentials
   - The user needs CREATE TABLE permissions

3. **Foreign key constraint error**
   - Make sure users and resumes tables exist first
   - These should already exist in production

## After Successful Migration

The candidate submission feature will work immediately:
- Request Update button will function
- Invite New Candidate will work
- Submission links will be valid

No restart required!