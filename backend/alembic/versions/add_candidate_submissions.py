"""add candidate submissions tables

Revision ID: add_candidate_submissions
Revises: add_interview_mode_fields
Create Date: 2024-12-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_candidate_submissions'
down_revision = 'add_interview_mode_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create enums if they don't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE submissiontype AS ENUM ('update', 'new');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE submissionstatus AS ENUM ('pending', 'submitted', 'processed', 'expired', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create invitation_campaigns table
    op.create_table('invitation_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('recruiter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=True),
        sa.Column('public_slug', sa.String(length=100), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True, default=False),
        sa.Column('email_template', sa.Text(), nullable=True),
        sa.Column('branding', sa.JSON(), nullable=True),
        sa.Column('auto_close_date', sa.DateTime(), nullable=True),
        sa.Column('max_submissions', sa.Integer(), nullable=True),
        sa.Column('stats', sa.JSON(), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['recruiter_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invitation_campaigns_public_slug'), 'invitation_campaigns', ['public_slug'], unique=True)
    
    # Create candidate_submissions table
    op.create_table('candidate_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('submission_type', postgresql.ENUM('update', 'new', name='submissiontype'), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'submitted', 'processed', 'expired', 'cancelled', name='submissionstatus'), nullable=False, default='pending'),
        sa.Column('recruiter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('resume_file_url', sa.String(length=500), nullable=True),
        sa.Column('resume_text', sa.Text(), nullable=True),
        sa.Column('parsed_data', sa.JSON(), nullable=True),
        sa.Column('availability', sa.String(length=50), nullable=True),
        sa.Column('salary_expectations', sa.JSON(), nullable=True),
        sa.Column('location_preferences', sa.JSON(), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('linkedin_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('email_sent_at', sa.DateTime(), nullable=True),
        sa.Column('email_opened_at', sa.DateTime(), nullable=True),
        sa.Column('link_clicked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['invitation_campaigns.id'], ),
        sa.ForeignKeyConstraint(['recruiter_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_candidate_submissions_token'), 'candidate_submissions', ['token'], unique=True)
    op.create_index(op.f('ix_candidate_submissions_recruiter_id'), 'candidate_submissions', ['recruiter_id'])
    op.create_index(op.f('ix_candidate_submissions_email'), 'candidate_submissions', ['email'])
    op.create_index(op.f('ix_candidate_submissions_status'), 'candidate_submissions', ['status'])


def downgrade():
    op.drop_index(op.f('ix_candidate_submissions_status'), table_name='candidate_submissions')
    op.drop_index(op.f('ix_candidate_submissions_email'), table_name='candidate_submissions')
    op.drop_index(op.f('ix_candidate_submissions_recruiter_id'), table_name='candidate_submissions')
    op.drop_index(op.f('ix_candidate_submissions_token'), table_name='candidate_submissions')
    op.drop_table('candidate_submissions')
    
    op.drop_index(op.f('ix_invitation_campaigns_public_slug'), table_name='invitation_campaigns')
    op.drop_table('invitation_campaigns')
    
    # Drop enums
    op.execute("DROP TYPE submissionstatus")
    op.execute("DROP TYPE submissiontype")