"""add interview pipeline tables

Revision ID: 004_add_interview_pipeline_tables
Revises: 003_add_interview_tables
Create Date: 2025-01-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_pipelines'
down_revision = '003_add_interview_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create interview_pipelines table
    op.create_table('interview_pipelines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('job_role', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('stages', sa.JSON(), nullable=True),
        sa.Column('scoring_weights', sa.JSON(), nullable=True),
        sa.Column('min_overall_score', sa.Integer(), nullable=True),
        sa.Column('auto_reject_on_fail', sa.Boolean(), nullable=True),
        sa.Column('auto_approve_on_pass', sa.Boolean(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create candidate_journeys table
    op.create_table('candidate_journeys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pipeline_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_position', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('current_stage', sa.String(), nullable=True),
        sa.Column('completed_stages', sa.JSON(), nullable=True),
        sa.Column('stage_results', sa.JSON(), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('final_recommendation', sa.String(), nullable=True),
        sa.Column('rejection_reason', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pipeline_id'], ['interview_pipelines.id'], ),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add journey_id to interview_sessions table
    op.add_column('interview_sessions', 
        sa.Column('journey_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_interview_sessions_journey_id', 
        'interview_sessions', 
        'candidate_journeys', 
        ['journey_id'], 
        ['id']
    )
    
    # Create indexes
    op.create_index('ix_interview_pipelines_job_role', 'interview_pipelines', ['job_role'])
    op.create_index('ix_interview_pipelines_is_active', 'interview_pipelines', ['is_active'])
    op.create_index('ix_candidate_journeys_resume_id', 'candidate_journeys', ['resume_id'])
    op.create_index('ix_candidate_journeys_pipeline_id', 'candidate_journeys', ['pipeline_id'])
    op.create_index('ix_candidate_journeys_status', 'candidate_journeys', ['status'])
    
    # Create default pipelines
    op.execute("""
        INSERT INTO interview_pipelines (id, name, description, job_role, is_active, stages, min_overall_score, created_at, updated_at)
        VALUES 
        (
            gen_random_uuid(),
            'Standard Software Engineer Pipeline',
            'Standard interview process for software engineering roles',
            'Software Engineer',
            true,
            '[
                {"order": 1, "name": "Phone Screen", "type": "general", "required": true, "min_score": 3.0, "prerequisites": []},
                {"order": 2, "name": "Technical Assessment", "type": "technical", "required": true, "min_score": 3.5, "prerequisites": ["Phone Screen"]},
                {"order": 3, "name": "Behavioral Interview", "type": "behavioral", "required": true, "min_score": 3.0, "prerequisites": ["Technical Assessment"]},
                {"order": 4, "name": "Final Round", "type": "final", "required": true, "min_score": 3.5, "prerequisites": ["Behavioral Interview"]}
            ]',
            3,
            NOW(),
            NOW()
        ),
        (
            gen_random_uuid(),
            'Product Manager Pipeline',
            'Interview process for product management roles',
            'Product Manager',
            true,
            '[
                {"order": 1, "name": "Initial Screen", "type": "general", "required": true, "min_score": 3.0, "prerequisites": []},
                {"order": 2, "name": "Product Case Study", "type": "technical", "required": true, "min_score": 3.5, "prerequisites": ["Initial Screen"]},
                {"order": 3, "name": "Leadership Assessment", "type": "behavioral", "required": true, "min_score": 3.5, "prerequisites": ["Initial Screen"]},
                {"order": 4, "name": "Executive Interview", "type": "final", "required": true, "min_score": 4.0, "prerequisites": ["Product Case Study", "Leadership Assessment"]}
            ]',
            3,
            NOW(),
            NOW()
        );
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_candidate_journeys_status', table_name='candidate_journeys')
    op.drop_index('ix_candidate_journeys_pipeline_id', table_name='candidate_journeys')
    op.drop_index('ix_candidate_journeys_resume_id', table_name='candidate_journeys')
    op.drop_index('ix_interview_pipelines_is_active', table_name='interview_pipelines')
    op.drop_index('ix_interview_pipelines_job_role', table_name='interview_pipelines')
    
    # Remove journey_id from interview_sessions
    op.drop_constraint('fk_interview_sessions_journey_id', 'interview_sessions', type_='foreignkey')
    op.drop_column('interview_sessions', 'journey_id')
    
    # Drop tables
    op.drop_table('candidate_journeys')
    op.drop_table('interview_pipelines')