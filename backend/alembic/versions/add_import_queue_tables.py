"""Add import queue tables for bulk imports

Revision ID: add_import_queue
Revises: 
Create Date: 2025-01-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_import_queue'
down_revision = 'add_fulltext_search'
branch_labels = None
depends_on = None


def upgrade():
    # Create import_queue table
    op.create_table('import_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('profile_data', sa.JSON(), nullable=False),
        sa.Column('source', sa.Enum('manual', 'extension', 'csv_upload', 'excel_upload', 'zip_archive', 'webhook', name='importsource'), nullable=True),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='importstatus'), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=True, default=0),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_queue_status'), 'import_queue', ['status'], unique=False)
    op.create_index(op.f('ix_import_queue_user_id'), 'import_queue', ['user_id'], unique=False)
    op.create_index(op.f('ix_import_queue_created_at'), 'import_queue', ['created_at'], unique=False)

    # Create import_history table
    op.create_table('import_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('imported_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_history_user_id'), 'import_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_import_history_imported_at'), 'import_history', ['imported_at'], unique=False)
    op.create_index(op.f('ix_import_history_source'), 'import_history', ['source'], unique=False)


def downgrade():
    # Drop indexes first
    op.drop_index(op.f('ix_import_history_source'), table_name='import_history')
    op.drop_index(op.f('ix_import_history_imported_at'), table_name='import_history')
    op.drop_index(op.f('ix_import_history_user_id'), table_name='import_history')
    op.drop_index(op.f('ix_import_queue_created_at'), table_name='import_queue')
    op.drop_index(op.f('ix_import_queue_user_id'), table_name='import_queue')
    op.drop_index(op.f('ix_import_queue_status'), table_name='import_queue')
    
    # Drop tables
    op.drop_table('import_history')
    op.drop_table('import_queue')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS importstatus')
    op.execute('DROP TYPE IF EXISTS importsource')