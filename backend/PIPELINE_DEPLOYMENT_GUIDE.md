# Pipeline & Workflow Management - Production Deployment Guide

## Overview
This guide contains all the SQL scripts needed to deploy the Pipeline & Workflow Management feature to production. Execute these scripts in order to properly set up the database schema and migrate existing data.

## Prerequisites
- PostgreSQL 14+ with UUID support (`gen_random_uuid()` function)
- Superuser or appropriate database permissions
- Backup of production database before running migrations

## Deployment Order

### Phase 1: Create Core Pipeline Tables and Types

#### 1.1 Create Pipeline Tables (Main Script)
**File:** `create_pipeline_tables_simple.sql`
**Purpose:** Creates all pipeline-related tables, enums, and indexes
**Tables Created:**
- `pipelines` - Pipeline workflow templates
- `candidate_pipeline_states` - Track candidate positions in pipelines
- `pipeline_activities` - Activity audit log
- `candidate_notes` - Collaborative notes on candidates
- `candidate_evaluations` - Interview feedback
- `candidate_communications` - Email/communication tracking
- `pipeline_automations` - Automation rules
- `pipeline_team_members` - Team permissions

**Enums Created:**
- `pipeline_stage_type` - Standard stage types
- `pipeline_activity_type` - Activity tracking types

**Important Notes:**
- Uses `DO $$ BEGIN ... EXCEPTION` blocks to handle existing types gracefully
- Creates indexes for all foreign keys and commonly queried fields
- Inserts a default pipeline template automatically

### Phase 2: Link Interviews to Pipeline States

#### 2.1 Add Pipeline State to Interview Sessions
**File:** `add_pipeline_state_to_interviews.sql`
**Purpose:** Links interview sessions to pipeline states
**Changes:**
- Adds `pipeline_state_id` column to `interview_sessions` table
- Creates foreign key constraint to `candidate_pipeline_states`
- Adds index for performance

### Phase 3: Create Automation Triggers

#### 3.1 Interview Scheduling Trigger
**File:** `complete_trigger_script.sql`
**Purpose:** Automatically moves candidates to interview stage when interviews are scheduled
**Creates:**
- Function `move_candidate_to_interview_on_schedule()`
- Trigger `interview_scheduled_move_to_interview`
- Logs activities when candidates are moved

### Phase 4: Insert Default Data

#### 4.1 Create Default Pipeline
**File:** `insert_default_pipeline.sql`
**Purpose:** Ensures a default pipeline exists for the organization
**Creates:**
- Default pipeline with stages: Applied → Screening → Interview → Offer → Hired
- Only inserts if no default pipeline exists

#### 4.2 Add Rejected/Withdrawn Stages
**File:** `update_pipeline_add_rejected_stages.sql`
**Purpose:** Adds terminal stages for rejected/withdrawn candidates
**Updates:**
- Adds "Rejected" and "Withdrawn" stages to existing pipelines
- These are terminal stages where candidates end their journey

### Phase 5: Data Migration and Fixes

#### 5.1 Fix Missing Interview Ratings
**File:** `fix_missing_ratings.sql`
**Purpose:** Calculates ratings for completed interviews that lack them
**Actions:**
- Calculates overall ratings from question responses
- Sets appropriate recommendations based on ratings
- Updates pipeline stages based on interview outcomes

#### 5.2 Fix Pipeline Stage Assignments
**File:** `fix_all_pipeline_issues.sql`
**Purpose:** Ensures all candidates are in correct pipeline stages
**Actions:**
- Moves high-rated candidates (≥4.0) to Offer stage
- Moves low-rated candidates (<2.0) to Rejected stage
- Creates activity logs for all movements
- Validates final state consistency

## Production Deployment Steps

### Step 1: Pre-deployment
```bash
# 1. Backup production database
pg_dump -h production-host -U username -d database_name > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Test scripts on staging environment first
```

### Step 2: Execute Core Scripts
```sql
-- Run in this exact order:

-- 1. Create pipeline tables
\i create_pipeline_tables_simple.sql

-- 2. Add pipeline_state_id to interviews
\i add_pipeline_state_to_interviews.sql

-- 3. Create automation trigger
\i complete_trigger_script.sql

-- 4. Insert default pipeline
\i insert_default_pipeline.sql

-- 5. Add rejected/withdrawn stages
\i update_pipeline_add_rejected_stages.sql
```

### Step 3: Data Migration
```sql
-- Only run if you have existing interview data to migrate:

-- 1. Fix missing ratings
\i fix_missing_ratings.sql

-- 2. Fix pipeline stage assignments
\i fix_all_pipeline_issues.sql
```

### Step 4: Verification
```sql
-- Verify tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%pipeline%' OR table_name LIKE 'candidate_%'
ORDER BY table_name;

-- Verify default pipeline exists
SELECT id, name, is_default, jsonb_array_length(stages) as stage_count
FROM pipelines
WHERE is_default = true;

-- Check pipeline stages
SELECT jsonb_array_elements(stages) AS stage
FROM pipelines
WHERE is_default = true
ORDER BY (stage->>'order')::int;

-- Verify trigger exists
SELECT tgname, tgtype 
FROM pg_trigger 
WHERE tgname = 'interview_scheduled_move_to_interview';

-- Check candidate distribution across stages
SELECT 
    current_stage_id,
    COUNT(*) as candidate_count
FROM candidate_pipeline_states
WHERE is_active = true
GROUP BY current_stage_id
ORDER BY candidate_count DESC;
```

## Rollback Scripts

If you need to rollback the deployment:

```sql
-- Drop triggers first
DROP TRIGGER IF EXISTS interview_scheduled_move_to_interview ON interview_sessions;
DROP FUNCTION IF EXISTS move_candidate_to_interview_on_schedule();

-- Remove pipeline_state_id from interviews
ALTER TABLE interview_sessions DROP COLUMN IF EXISTS pipeline_state_id;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS pipeline_team_members CASCADE;
DROP TABLE IF EXISTS pipeline_automations CASCADE;
DROP TABLE IF EXISTS candidate_communications CASCADE;
DROP TABLE IF EXISTS candidate_evaluations CASCADE;
DROP TABLE IF EXISTS candidate_notes CASCADE;
DROP TABLE IF EXISTS pipeline_activities CASCADE;
DROP TABLE IF EXISTS candidate_pipeline_states CASCADE;
DROP TABLE IF EXISTS pipelines CASCADE;

-- Drop types
DROP TYPE IF EXISTS pipeline_activity_type CASCADE;
DROP TYPE IF EXISTS pipeline_stage_type CASCADE;
```

## Post-Deployment Tasks

1. **Monitor Performance:**
   - Check query performance on pipeline views
   - Monitor index usage with `pg_stat_user_indexes`

2. **Verify Data Integrity:**
   - Ensure all active candidates have pipeline states
   - Check for orphaned pipeline states

3. **Test Functionality:**
   - Create a test interview and verify trigger moves candidate
   - Test pipeline stage transitions
   - Verify activity logging

## Troubleshooting

### Common Issues:

1. **Type already exists error:**
   - The scripts use `DO $$ BEGIN ... EXCEPTION` blocks to handle this
   - If still occurring, manually check and drop the type

2. **Foreign key violations:**
   - Ensure users and resumes tables exist and have data
   - Check that referenced IDs are valid

3. **Trigger not firing:**
   - Verify trigger is enabled: `ALTER TRIGGER interview_scheduled_move_to_interview ON interview_sessions ENABLE;`
   - Check that pipeline_state_id is being set on new interviews

4. **Performance issues:**
   - Run `ANALYZE` on new tables after data migration
   - Check that all indexes were created successfully

## Support Queries

### Check system health:
```sql
-- Pipeline system health check
SELECT 
    'Pipelines' as component,
    COUNT(*) as count,
    CASE WHEN COUNT(*) > 0 THEN 'OK' ELSE 'MISSING' END as status
FROM pipelines
UNION ALL
SELECT 
    'Active Candidate States',
    COUNT(*),
    CASE WHEN COUNT(*) > 0 THEN 'OK' ELSE 'WARNING' END
FROM candidate_pipeline_states
WHERE is_active = true
UNION ALL
SELECT 
    'Pipeline Activities (Last 7 days)',
    COUNT(*),
    CASE WHEN COUNT(*) > 0 THEN 'OK' ELSE 'WARNING' END
FROM pipeline_activities
WHERE created_at > NOW() - INTERVAL '7 days';
```

## Required Environment Variables

Ensure the application has these environment variables set after deployment:
- `PIPELINE_FEATURE_ENABLED=true`
- `DEFAULT_PIPELINE_STAGES=applied,screening,interview,offer,hired,rejected,withdrawn`

## Contact

For issues during deployment, contact the development team with:
1. Error messages from script execution
2. Output of verification queries
3. Database version and configuration