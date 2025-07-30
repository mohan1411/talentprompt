"""Fix LinkedIn URL unique constraint to be user-specific

Revision ID: fix_linkedin_url_constraint
Revises: oauth_fields_001
Create Date: 2025-01-24 13:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_linkedin_url_constraint'
down_revision = 'add_interview_mode_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing unique constraint on linkedin_url
    op.drop_constraint('resumes_linkedin_url_key', 'resumes', type_='unique')
    
    # Create a new unique constraint on (user_id, linkedin_url)
    op.create_unique_constraint(
        'resumes_user_id_linkedin_url_key', 
        'resumes', 
        ['user_id', 'linkedin_url']
    )
    
    # Add an index on linkedin_url for query performance
    op.create_index(
        'idx_resumes_linkedin_url', 
        'resumes', 
        ['linkedin_url']
    )


def downgrade():
    # Remove the index
    op.drop_index('idx_resumes_linkedin_url', 'resumes')
    
    # Drop the composite unique constraint
    op.drop_constraint('resumes_user_id_linkedin_url_key', 'resumes', type_='unique')
    
    # Recreate the original unique constraint on linkedin_url
    # Note: This might fail if multiple users have imported the same profile
    op.create_unique_constraint(
        'resumes_linkedin_url_key', 
        'resumes', 
        ['linkedin_url']
    )