"""make password nullable for oauth users

Revision ID: make_password_nullable
Revises: oauth_fields
Create Date: 2025-07-19 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'make_password_nullable'
down_revision = 'add_candidate_submissions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make hashed_password nullable for OAuth users
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(),
                    nullable=True)


def downgrade() -> None:
    # Revert hashed_password to non-nullable
    # Note: This will fail if there are users with NULL passwords
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(),
                    nullable=False)