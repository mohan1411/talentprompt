"""Add full-text search indexes for hybrid search

Revision ID: add_fulltext_search
Revises: previous_revision
Create Date: 2025-01-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_fulltext_search'
down_revision = 'add_email_verification_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Add full-text search indexes and functions."""
    
    # Create GIN indexes for full-text search
    op.execute("""
        -- Create GIN index on raw_text column for fast text search
        CREATE INDEX IF NOT EXISTS idx_resumes_raw_text_gin 
        ON resumes USING GIN (to_tsvector('english', COALESCE(raw_text, '')));
        
        -- Create GIN index on summary column
        CREATE INDEX IF NOT EXISTS idx_resumes_summary_gin 
        ON resumes USING GIN (to_tsvector('english', COALESCE(summary, '')));
        
        -- Create GIN index on skills JSON column
        CREATE INDEX IF NOT EXISTS idx_resumes_skills_gin 
        ON resumes USING GIN (to_tsvector('english', COALESCE(skills::text, '')));
        
        -- Create composite GIN index for searching across multiple fields
        CREATE INDEX IF NOT EXISTS idx_resumes_composite_search_gin 
        ON resumes USING GIN (
            to_tsvector('english', 
                COALESCE(raw_text, '') || ' ' || 
                COALESCE(summary, '') || ' ' || 
                COALESCE(skills::text, '') || ' ' ||
                COALESCE(current_title, '')
            )
        );
        
        -- Create trigram index for fuzzy matching (requires pg_trgm extension)
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
        
        -- Trigram indexes for fuzzy skill matching
        CREATE INDEX IF NOT EXISTS idx_resumes_skills_trgm 
        ON resumes USING GIN ((skills::text) gin_trgm_ops);
        
        CREATE INDEX IF NOT EXISTS idx_resumes_current_title_trgm 
        ON resumes USING GIN (current_title gin_trgm_ops);
        
        -- Create index on user_id for filtering
        CREATE INDEX IF NOT EXISTS idx_resumes_user_id 
        ON resumes (user_id);
        
        -- Composite index for user_id for efficient filtering
        CREATE INDEX IF NOT EXISTS idx_resumes_user_status 
        ON resumes (user_id, status);
        
        -- Create a materialized view for pre-computed document stats (optional)
        CREATE MATERIALIZED VIEW IF NOT EXISTS resume_doc_stats AS
        SELECT 
            user_id,
            COUNT(*) as doc_count,
            AVG(LENGTH(COALESCE(raw_text, ''))) as avg_doc_length,
            MAX(updated_at) as last_update
        FROM resumes
        GROUP BY user_id;
        
        -- Create index on the materialized view
        CREATE INDEX IF NOT EXISTS idx_resume_doc_stats_user_id 
        ON resume_doc_stats (user_id);
    """)
    
    # Create helper functions for BM25 scoring
    op.execute("""
        -- Function to calculate term frequency
        CREATE OR REPLACE FUNCTION calculate_tf(doc_text TEXT, term TEXT)
        RETURNS FLOAT AS $$
        BEGIN
            RETURN (LENGTH(doc_text) - LENGTH(REPLACE(LOWER(doc_text), LOWER(term), ''))) / LENGTH(term);
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        
        -- Function to perform fuzzy skill matching
        CREATE OR REPLACE FUNCTION fuzzy_skill_match(query_skill TEXT, threshold FLOAT DEFAULT 0.3)
        RETURNS TABLE(resume_id UUID, similarity FLOAT) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                r.id as resume_id,
                similarity(query_skill, r.skills::text) as similarity
            FROM resumes r
            WHERE similarity(query_skill, r.skills::text) > threshold
            ORDER BY similarity DESC;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade():
    """Remove full-text search indexes and functions."""
    
    # Drop indexes
    op.execute("""
        DROP INDEX IF EXISTS idx_resumes_raw_text_gin;
        DROP INDEX IF EXISTS idx_resumes_summary_gin;
        DROP INDEX IF EXISTS idx_resumes_skills_gin;
        DROP INDEX IF EXISTS idx_resumes_composite_search_gin;
        DROP INDEX IF EXISTS idx_resumes_skills_trgm;
        DROP INDEX IF EXISTS idx_resumes_current_title_trgm;
        DROP INDEX IF EXISTS idx_resumes_user_id;
        DROP INDEX IF EXISTS idx_resumes_user_status;
        DROP INDEX IF EXISTS idx_resume_doc_stats_user_id;
    """)
    
    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS resume_doc_stats;")
    
    # Drop functions
    op.execute("""
        DROP FUNCTION IF EXISTS calculate_tf(TEXT, TEXT);
        DROP FUNCTION IF EXISTS fuzzy_skill_match(TEXT, FLOAT);
    """)