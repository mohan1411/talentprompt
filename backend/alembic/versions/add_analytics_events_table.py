"""add analytics events table

Revision ID: add_analytics_events
Revises: add_outreach_tables
Create Date: 2025-01-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_analytics_events'
down_revision = 'add_outreach_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create analytics_events table
    op.create_table('analytics_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('idx_analytics_events_user_id', 'analytics_events', ['user_id'])
    op.create_index('idx_analytics_events_event_type', 'analytics_events', ['event_type'])
    op.create_index('idx_analytics_events_created_at', 'analytics_events', ['created_at'])
    
    # Create composite index for common queries
    op.create_index('idx_analytics_events_type_date', 'analytics_events', ['event_type', 'created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_analytics_events_type_date', table_name='analytics_events')
    op.drop_index('idx_analytics_events_created_at', table_name='analytics_events')
    op.drop_index('idx_analytics_events_event_type', table_name='analytics_events')
    op.drop_index('idx_analytics_events_user_id', table_name='analytics_events')
    
    # Drop table
    op.drop_table('analytics_events')