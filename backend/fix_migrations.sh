#!/bin/bash

echo "Fixing migration files..."

cd /app/alembic/versions

# Remove all old migration files
rm -f *.py.bak
rm -f old_*.py

# Create initial migration that combines all tables
cat > 001_initial_migration.py << 'EOF'
"""Initial migration with all tables

Revision ID: 001_initial_migration
Revises: 
Create Date: 2025-07-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('company', sa.String(), nullable=True),
        sa.Column('job_title', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('timezone', sa.String(), default='UTC'),
        sa.Column('language', sa.String(), default='en'),
        sa.Column('supabase_id', sa.String(), nullable=True)
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_supabase_id', 'users', ['supabase_id'], unique=True)

    # Create resumes table
    op.create_table('resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('current_title', sa.String(), nullable=True),
        sa.Column('years_experience', sa.Integer(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('parsed_data', sa.JSON(), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('skills', sa.JSON(), nullable=True),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_type', sa.String(), nullable=True),
        sa.Column('job_position', sa.String(), nullable=True),
        sa.Column('linkedin_url', sa.String(), nullable=True),
        sa.Column('linkedin_data', sa.JSON(), nullable=True),
        sa.Column('last_linkedin_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), default='active'),
        sa.Column('parse_status', sa.String(), default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('parsed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('view_count', sa.Integer(), default=0),
        sa.Column('search_appearance_count', sa.Integer(), default=0),
        sa.Column('ai_analysis', sa.JSON(), nullable=True),
        sa.Column('match_scores', sa.JSON(), nullable=True)
    )
    op.create_index('ix_resumes_email', 'resumes', ['email'])
    op.create_index('ix_resumes_job_position', 'resumes', ['job_position'])
    op.create_index('ix_resumes_linkedin_url', 'resumes', ['linkedin_url'], unique=True)

    # Create interview_pipelines table
    op.create_table('interview_pipelines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('position_title', sa.String(), nullable=False),
        sa.Column('position_level', sa.String(), nullable=True),
        sa.Column('required_skills', sa.JSON(), nullable=True),
        sa.Column('nice_to_have_skills', sa.JSON(), nullable=True),
        sa.Column('stages', sa.JSON(), nullable=True),
        sa.Column('questions', sa.JSON(), nullable=True),
        sa.Column('evaluation_criteria', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )

    # Create interview_sessions table
    op.create_table('interview_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id'), nullable=False),
        sa.Column('pipeline_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('interview_pipelines.id'), nullable=True),
        sa.Column('interview_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('meeting_url', sa.String(), nullable=True),
        sa.Column('recording_url', sa.String(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('ai_notes', sa.JSON(), nullable=True),
        sa.Column('evaluation', sa.JSON(), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('recommendation', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )

    # Create interview_questions table
    op.create_table('interview_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('interview_sessions.id'), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('difficulty', sa.String(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('ai_evaluation', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # Create candidate_journeys table
    op.create_table('candidate_journeys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id'), nullable=False),
        sa.Column('pipeline_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('interview_pipelines.id'), nullable=True),
        sa.Column('current_stage', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('timeline', sa.JSON(), nullable=True),
        sa.Column('notes', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )

    # Create LinkedIn import history table
    op.create_table('linkedin_import_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id'), nullable=True),
        sa.Column('linkedin_url', sa.String(), nullable=False),
        sa.Column('import_status', sa.String(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('source', sa.String(), nullable=True)
    )
    op.create_index('ix_linkedin_import_history_user_id', 'linkedin_import_history', ['user_id'])
    op.create_index('ix_linkedin_import_history_created_at', 'linkedin_import_history', ['created_at'])


def downgrade() -> None:
    op.drop_table('linkedin_import_history')
    op.drop_table('candidate_journeys')
    op.drop_table('interview_questions')
    op.drop_table('interview_sessions')
    op.drop_table('interview_pipelines')
    op.drop_table('resumes')
    op.drop_table('users')
EOF

# Remove the old migrations
rm -f 003_add_interview_tables.py
rm -f 004_add_interview_pipeline_tables.py
rm -f 005_add_linkedin_fields.py

echo "Migration files fixed!"