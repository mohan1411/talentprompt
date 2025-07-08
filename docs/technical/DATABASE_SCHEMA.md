# TalentPrompt Database Schema

## 1. Overview

TalentPrompt uses PostgreSQL as the primary database with pgvector extension for vector operations. This document describes the complete database schema.

## 2. Database Configuration

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create custom types
CREATE TYPE user_role AS ENUM ('admin', 'recruiter', 'hiring_manager', 'viewer');
CREATE TYPE resume_status AS ENUM ('uploading', 'processing', 'completed', 'failed');
CREATE TYPE search_type AS ENUM ('prompt', 'structured', 'hybrid');
CREATE TYPE candidate_type AS ENUM ('internal', 'external', 'alumni', 'contractor');
```

## 3. Core Tables

### 3.1 Users and Authentication

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role user_role NOT NULL DEFAULT 'recruiter',
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    
    -- Profile information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    avatar_url TEXT,
    
    -- Metadata
    preferences JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMPTZ,
    
    -- Indexes
    INDEX idx_users_email (email),
    INDEX idx_users_role (role),
    INDEX idx_users_active (is_active)
);

-- User sessions
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_sessions_user (user_id),
    INDEX idx_sessions_token (token_hash),
    INDEX idx_sessions_expires (expires_at)
);

-- API keys for integrations
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    permissions JSONB DEFAULT '{}',
    rate_limit INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_api_keys_user (user_id),
    INDEX idx_api_keys_hash (key_hash)
);
```

### 3.2 Organizations and Teams

```sql
-- Organizations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    domain VARCHAR(255),
    
    -- Subscription
    plan VARCHAR(50) DEFAULT 'free',
    plan_expires_at TIMESTAMPTZ,
    
    -- Settings
    settings JSONB DEFAULT '{}',
    features JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_orgs_slug (slug),
    INDEX idx_orgs_domain (domain)
);

-- Organization members
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    joined_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(organization_id, user_id),
    INDEX idx_org_members_org (organization_id),
    INDEX idx_org_members_user (user_id)
);

-- Teams within organizations
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_teams_org (organization_id)
);

-- Team members
CREATE TABLE team_members (
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (team_id, user_id)
);
```

### 3.3 Resume Management

```sql
-- Resumes table
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    
    -- File information
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    mime_type VARCHAR(100),
    
    -- Processing status
    status resume_status NOT NULL DEFAULT 'uploading',
    error_message TEXT,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    
    -- Parsed data
    raw_text TEXT,
    parsed_data JSONB,
    
    -- Candidate information
    candidate_type candidate_type DEFAULT 'external',
    candidate_id UUID, -- Reference to candidates table
    
    -- Search optimization
    search_vector tsvector,
    embedding vector(1536), -- OpenAI embedding dimension
    
    -- Metadata
    source VARCHAR(50) DEFAULT 'upload',
    tags TEXT[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_resumes_org (organization_id),
    INDEX idx_resumes_status (status),
    INDEX idx_resumes_candidate (candidate_id),
    INDEX idx_resumes_hash (file_hash),
    INDEX idx_resumes_search USING GIN (search_vector),
    INDEX idx_resumes_embedding USING hnsw (embedding vector_cosine_ops),
    INDEX idx_resumes_tags USING GIN (tags)
);

-- Trigger to update search vector
CREATE OR REPLACE FUNCTION update_resume_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.raw_text, '') || ' ' ||
        COALESCE(NEW.parsed_data->>'skills', '') || ' ' ||
        COALESCE(NEW.parsed_data->>'experience', '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER resume_search_vector_trigger
BEFORE INSERT OR UPDATE ON resumes
FOR EACH ROW
EXECUTE FUNCTION update_resume_search_vector();
```

### 3.4 Candidates

```sql
-- Candidates (parsed from resumes)
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Contact information
    email VARCHAR(255),
    phone VARCHAR(50),
    name VARCHAR(255),
    location VARCHAR(255),
    linkedin_url TEXT,
    github_url TEXT,
    portfolio_url TEXT,
    
    -- Professional information
    current_title VARCHAR(255),
    current_company VARCHAR(255),
    years_experience INTEGER,
    
    -- Parsed data
    summary TEXT,
    skills JSONB,
    experience JSONB,
    education JSONB,
    certifications JSONB,
    languages JSONB,
    
    -- Analysis
    seniority_level VARCHAR(50),
    specializations TEXT[],
    industry_experience TEXT[],
    
    -- Internal candidate fields
    employee_id VARCHAR(100),
    department VARCHAR(100),
    manager_id UUID REFERENCES users(id),
    hire_date DATE,
    
    -- Search and matching
    embedding vector(1536),
    search_vector tsvector,
    
    -- Metadata
    source VARCHAR(50),
    tags TEXT[],
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMPTZ,
    
    -- Indexes
    INDEX idx_candidates_org (organization_id),
    INDEX idx_candidates_email (email),
    INDEX idx_candidates_embedding USING hnsw (embedding vector_cosine_ops),
    INDEX idx_candidates_search USING GIN (search_vector),
    INDEX idx_candidates_skills USING GIN (skills),
    INDEX idx_candidates_experience_years (years_experience)
);

-- Link resumes to candidates
ALTER TABLE resumes 
ADD CONSTRAINT fk_resume_candidate 
FOREIGN KEY (candidate_id) 
REFERENCES candidates(id) 
ON DELETE SET NULL;
```

### 3.5 Search and Analytics

```sql
-- Search queries
CREATE TABLE searches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Search details
    query TEXT NOT NULL,
    search_type search_type NOT NULL DEFAULT 'prompt',
    filters JSONB DEFAULT '{}',
    
    -- Results
    result_count INTEGER,
    results JSONB,
    facets JSONB,
    
    -- Performance
    processing_time_ms INTEGER,
    search_method VARCHAR(50),
    
    -- User interaction
    refinements JSONB DEFAULT '[]',
    selected_results UUID[] DEFAULT '{}',
    
    -- Metadata
    source VARCHAR(50) DEFAULT 'web',
    session_id UUID,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_searches_org (organization_id),
    INDEX idx_searches_user (user_id),
    INDEX idx_searches_created (created_at),
    INDEX idx_searches_session (session_id)
);

-- Search analytics
CREATE TABLE search_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_id UUID NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
    
    -- Performance metrics
    query_parse_time_ms INTEGER,
    embedding_time_ms INTEGER,
    search_time_ms INTEGER,
    ranking_time_ms INTEGER,
    
    -- Quality metrics
    relevance_scores JSONB,
    click_through_rate DECIMAL(5,4),
    
    -- User actions
    results_clicked UUID[],
    results_saved UUID[],
    time_to_first_click_ms INTEGER,
    
    -- A/B testing
    experiment_id VARCHAR(100),
    variant VARCHAR(50),
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_search_analytics_search (search_id),
    INDEX idx_search_analytics_experiment (experiment_id)
);
```

### 3.6 Lists and Collaboration

```sql
-- Candidate lists
CREATE TABLE candidate_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    
    -- List details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    list_type VARCHAR(50) DEFAULT 'shortlist',
    
    -- Sharing
    visibility VARCHAR(50) DEFAULT 'private',
    shared_with_teams UUID[] DEFAULT '{}',
    shared_with_users UUID[] DEFAULT '{}',
    
    -- Metadata
    tags TEXT[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_lists_org (organization_id),
    INDEX idx_lists_creator (created_by)
);

-- List members
CREATE TABLE candidate_list_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    list_id UUID NOT NULL REFERENCES candidate_lists(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
    
    -- Member details
    added_by UUID NOT NULL REFERENCES users(id),
    notes TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Timestamps
    added_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(list_id, candidate_id),
    INDEX idx_list_members_list (list_id),
    INDEX idx_list_members_candidate (candidate_id)
);

-- Comments on candidates
CREATE TABLE candidate_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    parent_id UUID REFERENCES candidate_comments(id) ON DELETE CASCADE,
    
    comment TEXT NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_comments_candidate (candidate_id),
    INDEX idx_comments_user (user_id),
    INDEX idx_comments_parent (parent_id)
);
```

### 3.7 Jobs and Applications

```sql
-- Jobs (for matching)
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    
    -- Job details
    title VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    location VARCHAR(255),
    remote_type VARCHAR(50) DEFAULT 'onsite',
    
    -- Requirements
    description TEXT,
    requirements JSONB,
    preferred_qualifications JSONB,
    
    -- Compensation
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency VARCHAR(3) DEFAULT 'USD',
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft',
    published_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    
    -- Search optimization
    embedding vector(1536),
    search_vector tsvector,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_jobs_org (organization_id),
    INDEX idx_jobs_status (status),
    INDEX idx_jobs_embedding USING hnsw (embedding vector_cosine_ops)
);

-- Applications (candidate-job matches)
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    
    -- Application details
    source VARCHAR(50) DEFAULT 'ai_match',
    match_score DECIMAL(5,4),
    match_explanation JSONB,
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'new',
    stage VARCHAR(50) DEFAULT 'screening',
    
    -- Timestamps
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(job_id, candidate_id),
    INDEX idx_applications_job (job_id),
    INDEX idx_applications_candidate (candidate_id),
    INDEX idx_applications_status (status)
);
```

### 3.8 System and Audit Tables

```sql
-- Audit log (Enhanced for EU AI Act compliance)
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    
    -- Action details
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    
    -- AI decision tracking (NEW)
    ai_model_used VARCHAR(100),
    ai_decision_id UUID,
    ai_confidence_score DECIMAL(5,4),
    
    -- Change details
    old_values JSONB,
    new_values JSONB,
    
    -- Request context
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_org (organization_id),
    INDEX idx_audit_resource (resource_type, resource_id),
    INDEX idx_audit_created (created_at),
    INDEX idx_audit_ai_decision (ai_decision_id)
);

-- AI Decision Transparency (NEW for EU AI Act)
CREATE TABLE ai_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    -- Decision details
    decision_type VARCHAR(50) NOT NULL,
    ai_model VARCHAR(100) NOT NULL,
    model_version VARCHAR(50),
    
    -- Input/Output
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    decision_factors JSONB NOT NULL,
    
    -- Transparency
    explanation TEXT NOT NULL,
    confidence_score DECIMAL(5,4),
    bias_check_result JSONB,
    
    -- Human oversight
    human_review_required BOOLEAN DEFAULT false,
    human_reviewed_at TIMESTAMPTZ,
    human_reviewed_by UUID REFERENCES users(id),
    human_override BOOLEAN DEFAULT false,
    
    -- Contestability
    is_contestable BOOLEAN DEFAULT true,
    contested_at TIMESTAMPTZ,
    contest_reason TEXT,
    contest_resolution TEXT,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_ai_decisions_org (organization_id),
    INDEX idx_ai_decisions_type (decision_type),
    INDEX idx_ai_decisions_created (created_at)
);

-- Bias Monitoring (NEW)
CREATE TABLE bias_monitoring (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    check_date DATE NOT NULL,
    
    -- Metrics
    protected_attribute VARCHAR(50) NOT NULL,
    fairness_score DECIMAL(5,4),
    disparate_impact_ratio DECIMAL(5,4),
    
    -- Details
    sample_size INTEGER,
    findings JSONB,
    actions_taken TEXT,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_bias_monitoring_date (check_date),
    INDEX idx_bias_monitoring_attribute (protected_attribute)
);

-- Background jobs
CREATE TABLE background_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Job data
    payload JSONB NOT NULL,
    result JSONB,
    error TEXT,
    
    -- Execution details
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    
    -- Scheduling
    scheduled_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_jobs_status (status),
    INDEX idx_jobs_scheduled (scheduled_at),
    INDEX idx_jobs_type (job_type)
);

-- Feature flags
CREATE TABLE feature_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    
    -- Targeting
    enabled BOOLEAN DEFAULT false,
    rollout_percentage INTEGER DEFAULT 0,
    
    -- Rules
    user_ids UUID[] DEFAULT '{}',
    organization_ids UUID[] DEFAULT '{}',
    rules JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_flags_name (name),
    INDEX idx_flags_enabled (enabled)
);
```

## 4. Views and Materialized Views

```sql
-- Active users view
CREATE VIEW active_users AS
SELECT 
    u.*,
    o.name as organization_name,
    o.plan as organization_plan
FROM users u
LEFT JOIN organization_members om ON u.id = om.user_id
LEFT JOIN organizations o ON om.organization_id = o.id
WHERE u.is_active = true;

-- Search performance view
CREATE MATERIALIZED VIEW search_performance_daily AS
SELECT 
    DATE(created_at) as date,
    organization_id,
    COUNT(*) as total_searches,
    AVG(processing_time_ms) as avg_processing_time,
    AVG(result_count) as avg_results,
    COUNT(DISTINCT user_id) as unique_users
FROM searches
GROUP BY DATE(created_at), organization_id;

CREATE INDEX idx_search_perf_date ON search_performance_daily(date);
CREATE INDEX idx_search_perf_org ON search_performance_daily(organization_id);

-- Refresh materialized view daily
CREATE OR REPLACE FUNCTION refresh_search_performance()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY search_performance_daily;
END;
$$ LANGUAGE plpgsql;
```

## 5. Functions and Triggers

```sql
-- Update timestamps trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- Repeat for other tables...

-- Calculate candidate match score
CREATE OR REPLACE FUNCTION calculate_match_score(
    job_embedding vector,
    candidate_embedding vector,
    required_skills jsonb,
    candidate_skills jsonb
) RETURNS DECIMAL AS $$
DECLARE
    vector_similarity DECIMAL;
    skill_match_score DECIMAL;
    final_score DECIMAL;
BEGIN
    -- Calculate cosine similarity
    vector_similarity := 1 - (job_embedding <=> candidate_embedding);
    
    -- Calculate skill match percentage
    -- Implementation details...
    
    -- Weighted final score
    final_score := (vector_similarity * 0.6) + (skill_match_score * 0.4);
    
    RETURN final_score;
END;
$$ LANGUAGE plpgsql;
```

## 6. Indexes Strategy

```sql
-- Performance-critical indexes
CREATE INDEX CONCURRENTLY idx_resumes_org_status 
ON resumes(organization_id, status) 
WHERE status = 'completed';

CREATE INDEX CONCURRENTLY idx_candidates_skills_experience 
ON candidates(organization_id, years_experience) 
WHERE years_experience IS NOT NULL;

-- Full-text search indexes
CREATE INDEX CONCURRENTLY idx_resumes_fulltext 
ON resumes USING GIN (search_vector);

CREATE INDEX CONCURRENTLY idx_candidates_fulltext 
ON candidates USING GIN (search_vector);

-- JSONB indexes for common queries
CREATE INDEX CONCURRENTLY idx_candidates_skills_gin 
ON candidates USING GIN (skills);

CREATE INDEX CONCURRENTLY idx_searches_filters_gin 
ON searches USING GIN (filters);
```

## 7. Partitioning Strategy

```sql
-- Partition searches table by month
CREATE TABLE searches_2024_01 PARTITION OF searches
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE searches_2024_02 PARTITION OF searches
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Automated partition creation
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
BEGIN
    partition_date := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month');
    partition_name := 'searches_' || TO_CHAR(partition_date, 'YYYY_MM');
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF searches 
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name,
                    partition_date,
                    partition_date + INTERVAL '1 month');
END;
$$ LANGUAGE plpgsql;
```

## 8. Security Considerations

```sql
-- Row-level security for multi-tenancy
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;

CREATE POLICY resumes_organization_policy ON resumes
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

-- Encrypt sensitive data
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Example: Encrypt API keys
CREATE OR REPLACE FUNCTION encrypt_api_key(key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(pgp_sym_encrypt(key, current_setting('app.encryption_key')), 'base64');
END;
$$ LANGUAGE plpgsql;
```

---

**Document Version**: 1.0
**Last Updated**: [Date]
**Database Version**: PostgreSQL 14+
**Required Extensions**: uuid-ossp, pgcrypto, pg_trgm, vector