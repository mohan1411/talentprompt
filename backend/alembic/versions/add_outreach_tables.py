"""Add outreach messages and templates tables

Revision ID: add_outreach_tables
Revises: add_import_queue_tables
Create Date: 2025-01-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_outreach_tables'
down_revision = 'add_import_queue'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    op.execute("CREATE TYPE messagestyle AS ENUM ('casual', 'professional', 'technical')")
    op.execute("CREATE TYPE messagestatus AS ENUM ('generated', 'sent', 'opened', 'responded', 'not_interested')")
    
    # Create outreach_messages table
    op.create_table('outreach_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('style', postgresql.ENUM('casual', 'professional', 'technical', name='messagestyle'), nullable=False),
        sa.Column('job_title', sa.String(255), nullable=True),
        sa.Column('job_requirements', sa.JSON(), nullable=True),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('status', postgresql.ENUM('generated', 'sent', 'opened', 'responded', 'not_interested', name='messagestatus'), server_default='generated', nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('response_rate', sa.Float(), nullable=True),
        sa.Column('generation_prompt', sa.Text(), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create outreach_templates table
    op.create_table('outreach_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('subject_template', sa.String(500), nullable=True),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('style', postgresql.ENUM('casual', 'professional', 'technical', name='messagestyle'), nullable=False),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('role_level', sa.String(50), nullable=True),
        sa.Column('job_function', sa.String(100), nullable=True),
        sa.Column('times_used', sa.Integer(), server_default='0', nullable=True),
        sa.Column('avg_response_rate', sa.Float(), nullable=True),
        sa.Column('is_public', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_outreach_messages_user_id', 'outreach_messages', ['user_id'])
    op.create_index('idx_outreach_messages_resume_id', 'outreach_messages', ['resume_id'])
    op.create_index('idx_outreach_messages_status', 'outreach_messages', ['status'])
    op.create_index('idx_outreach_messages_created_at', 'outreach_messages', ['created_at'])
    
    op.create_index('idx_outreach_templates_user_id', 'outreach_templates', ['user_id'])
    op.create_index('idx_outreach_templates_is_public', 'outreach_templates', ['is_public'])
    op.create_index('idx_outreach_templates_style', 'outreach_templates', ['style'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_outreach_templates_style', table_name='outreach_templates')
    op.drop_index('idx_outreach_templates_is_public', table_name='outreach_templates')
    op.drop_index('idx_outreach_templates_user_id', table_name='outreach_templates')
    
    op.drop_index('idx_outreach_messages_created_at', table_name='outreach_messages')
    op.drop_index('idx_outreach_messages_status', table_name='outreach_messages')
    op.drop_index('idx_outreach_messages_resume_id', table_name='outreach_messages')
    op.drop_index('idx_outreach_messages_user_id', table_name='outreach_messages')
    
    # Drop tables
    op.drop_table('outreach_templates')
    op.drop_table('outreach_messages')
    
    # Drop enum types
    op.execute('DROP TYPE messagestatus')
    op.execute('DROP TYPE messagestyle')