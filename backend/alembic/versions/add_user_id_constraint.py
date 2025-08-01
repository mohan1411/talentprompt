"""Add NOT NULL constraint to resume.user_id

Revision ID: add_user_id_constraint
Revises: add_import_queue_tables
Create Date: 2025-08-01 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_user_id_constraint'
down_revision = 'add_import_queue_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add NOT NULL constraint to resume.user_id after fixing orphaned resumes."""
    
    # First, update any NULL user_ids to a default user
    # This is a safety measure - in production, you should identify a proper user
    op.execute("""
        UPDATE resumes 
        SET user_id = (
            SELECT id FROM users 
            WHERE is_active = true 
            ORDER BY created_at 
            LIMIT 1
        )
        WHERE user_id IS NULL
    """)
    
    # Now add the NOT NULL constraint
    op.alter_column('resumes', 'user_id',
                    existing_type=postgresql.UUID(),
                    nullable=False)
    
    # Also ensure the foreign key constraint exists
    # Check if constraint already exists first
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'resumes_user_id_fkey'
            ) THEN
                ALTER TABLE resumes 
                ADD CONSTRAINT resumes_user_id_fkey 
                FOREIGN KEY (user_id) 
                REFERENCES users(id) 
                ON DELETE CASCADE;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove NOT NULL constraint from resume.user_id."""
    op.alter_column('resumes', 'user_id',
                    existing_type=postgresql.UUID(),
                    nullable=True)