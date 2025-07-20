"""Add OAuth fields to user model

Revision ID: oauth_fields_001
Revises: 
Create Date: 2025-07-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'oauth_fields_001'
down_revision = 'add_analytics_events'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add OAuth fields to users table
    op.add_column('users', sa.Column('oauth_provider', sa.String(), nullable=True))
    op.add_column('users', sa.Column('oauth_provider_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('oauth_data', sa.String(), nullable=True))
    
    # Create index for faster OAuth lookups
    op.create_index('ix_users_oauth_provider', 'users', ['oauth_provider'])
    op.create_index('ix_users_oauth_provider_id', 'users', ['oauth_provider_id'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_users_oauth_provider_id', table_name='users')
    op.drop_index('ix_users_oauth_provider', table_name='users')
    
    # Remove OAuth fields
    op.drop_column('users', 'oauth_data')
    op.drop_column('users', 'oauth_provider_id')
    op.drop_column('users', 'oauth_provider')