"""Add interview mode fields

Revision ID: add_interview_mode_fields
Revises: oauth_fields_migration
Create Date: 2025-07-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_interview_mode_fields'
down_revision = 'oauth_fields_migration'
branch_labels = None
depends_on = None


def upgrade():
    # Add interview_category column to interview_sessions
    op.add_column('interview_sessions', 
        sa.Column('interview_category', sa.String(), nullable=True)
    )
    
    # Add interview_mode as an enum type
    interview_mode_enum = sa.Enum('IN_PERSON', 'VIRTUAL', 'PHONE', name='interviewmode')
    interview_mode_enum.create(op.get_bind(), checkfirst=True)
    
    # Update the interview_type column to use the enum
    op.execute("ALTER TABLE interview_sessions ALTER COLUMN interview_type TYPE VARCHAR USING interview_type::text")
    op.alter_column('interview_sessions', 'interview_type',
                    type_=interview_mode_enum,
                    postgresql_using='interview_type::interviewmode',
                    nullable=True)


def downgrade():
    # Change interview_type back to string
    op.alter_column('interview_sessions', 'interview_type',
                    type_=sa.String(),
                    nullable=True)
    
    # Drop the enum type
    interview_mode_enum = sa.Enum('IN_PERSON', 'VIRTUAL', 'PHONE', name='interviewmode')
    interview_mode_enum.drop(op.get_bind(), checkfirst=True)
    
    # Remove interview_category column
    op.drop_column('interview_sessions', 'interview_category')