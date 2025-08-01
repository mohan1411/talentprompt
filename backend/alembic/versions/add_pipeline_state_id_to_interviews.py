"""Add pipeline_state_id to interview_sessions

Revision ID: add_pipeline_state_id_to_interviews
Revises: add_interview_mode_fields
Create Date: 2025-08-01 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_pipeline_state_id_to_interviews'
down_revision = 'add_interview_mode_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add pipeline_state_id column to interview_sessions table
    op.add_column('interview_sessions', sa.Column('pipeline_state_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_interview_sessions_pipeline_state_id',
        'interview_sessions',
        'candidate_pipeline_states',
        ['pipeline_state_id'],
        ['id']
    )
    
    # Add index for performance
    op.create_index(
        'ix_interview_sessions_pipeline_state_id',
        'interview_sessions',
        ['pipeline_state_id']
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_interview_sessions_pipeline_state_id', table_name='interview_sessions')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_interview_sessions_pipeline_state_id', 'interview_sessions', type_='foreignkey')
    
    # Drop column
    op.drop_column('interview_sessions', 'pipeline_state_id')