# URGENT: Fix Candidate Submissions Tables

## Quick Fix - Run This SQL in Railway

1. Go to Railway Dashboard
2. Click on your PostgreSQL Database
3. Go to "Query" tab
4. Copy and paste this ENTIRE SQL:

```sql
-- Create tables WITHOUT foreign keys first
CREATE TABLE IF NOT EXISTS invitation_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL,
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

CREATE TABLE IF NOT EXISTS candidate_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(255) UNIQUE NOT NULL,
    submission_type VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    recruiter_id UUID NOT NULL,
    campaign_id UUID,
    resume_id UUID,
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
CREATE INDEX IF NOT EXISTS ix_candidate_submissions_token ON candidate_submissions(token);
CREATE INDEX IF NOT EXISTS ix_candidate_submissions_recruiter_id ON candidate_submissions(recruiter_id);
CREATE INDEX IF NOT EXISTS ix_candidate_submissions_email ON candidate_submissions(email);

-- Check if tables were created
SELECT COUNT(*) as tables_created
FROM information_schema.tables 
WHERE table_name IN ('candidate_submissions', 'invitation_campaigns');
```

5. Click "Run Query"

## Alternative: Use Any PostgreSQL Client

If you have TablePlus, pgAdmin, or any PostgreSQL client:

1. Connect using your Railway database credentials
2. Run the SQL above
3. Done!

## Get Your Database Credentials

From Railway:
1. Click on PostgreSQL database service
2. Go to "Connect" tab
3. You'll see:
   - Host
   - Port
   - Database
   - Username
   - Password

## Why This Is Happening

The Alembic migrations aren't running properly due to the migration chain issues. This SQL creates the tables directly without going through migrations.

## After Running the SQL

The candidate submission feature will work IMMEDIATELY. No restart needed!

Test it:
1. Go to your app
2. Click "Request Update" on any resume
3. It should work now!

## If Still Having Issues

Run this debug SQL to see what's wrong:

```sql
-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('candidate_submissions', 'invitation_campaigns');

-- Check your current user permissions
SELECT current_user, has_table_privilege(current_user, 'users', 'SELECT') as can_read;
```

The tables MUST be created for the feature to work!