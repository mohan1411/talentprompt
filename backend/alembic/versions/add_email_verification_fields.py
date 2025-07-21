"""Add email verification fields

Revision ID: add_email_verification_fields
Revises: 
Create Date: 2025-07-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_email_verification_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email verification fields to users table
    op.add_column('users', sa.Column('email_verification_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('email_verification_sent_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove email verification fields
    op.drop_column('users', 'email_verification_sent_at')
    op.drop_column('users', 'email_verification_token')