"""add interview tables

Revision ID: 003_add_interview_tables
Revises: 73c693e72071
Create Date: 2025-07-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_interview_tables'
down_revision = '73c693e72071'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types if they don't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE interviewstatus AS ENUM ('scheduled', 'in_progress', 'completed', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE questioncategory AS ENUM ('technical', 'behavioral', 'situational', 'culture_fit', 'experience', 'problem_solving');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create interview_sessions table
    op.create_table('interview_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interviewer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_position', sa.String(), nullable=False),
        sa.Column('job_requirements', sa.JSON(), nullable=True),
        sa.Column('interview_type', sa.String(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('status', postgresql.ENUM('scheduled', 'in_progress', 'completed', 'cancelled', name='interviewstatus'), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('preparation_notes', sa.JSON(), nullable=True),
        sa.Column('suggested_questions', sa.JSON(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recordings', sa.JSON(), nullable=True),
        sa.Column('scorecard', sa.JSON(), nullable=True),
        sa.Column('overall_rating', sa.Float(), nullable=True),
        sa.Column('recommendation', sa.String(), nullable=True),
        sa.Column('strengths', sa.JSON(), nullable=True),
        sa.Column('concerns', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['interviewer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create interview_questions table
    op.create_table('interview_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('category', postgresql.ENUM('technical', 'behavioral', 'situational', 'culture_fit', 'experience', 'problem_solving', name='questioncategory'), nullable=False),
        sa.Column('difficulty_level', sa.Integer(), nullable=True),
        sa.Column('ai_generated', sa.Boolean(), nullable=True),
        sa.Column('generation_context', sa.JSON(), nullable=True),
        sa.Column('expected_answer_points', sa.JSON(), nullable=True),
        sa.Column('asked', sa.Boolean(), nullable=True),
        sa.Column('asked_at', sa.DateTime(), nullable=True),
        sa.Column('response_summary', sa.Text(), nullable=True),
        sa.Column('response_rating', sa.Float(), nullable=True),
        sa.Column('follow_up_questions', sa.JSON(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('question_group', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create interview_feedback table
    op.create_table('interview_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('technical_rating', sa.Float(), nullable=True),
        sa.Column('communication_rating', sa.Float(), nullable=True),
        sa.Column('culture_fit_rating', sa.Float(), nullable=True),
        sa.Column('overall_rating', sa.Float(), nullable=True),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('weaknesses', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.String(), nullable=True),
        sa.Column('competency_ratings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create interview_templates table
    op.create_table('interview_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('job_role', sa.String(), nullable=True),
        sa.Column('required_skills', sa.JSON(), nullable=True),
        sa.Column('experience_level', sa.String(), nullable=True),
        sa.Column('question_categories', sa.JSON(), nullable=True),
        sa.Column('evaluation_criteria', sa.JSON(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('interview_stages', sa.JSON(), nullable=True),
        sa.Column('times_used', sa.Integer(), nullable=True),
        sa.Column('avg_success_rate', sa.Float(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_interview_sessions_interviewer_id', 'interview_sessions', ['interviewer_id'])
    op.create_index('ix_interview_sessions_resume_id', 'interview_sessions', ['resume_id'])
    op.create_index('ix_interview_sessions_status', 'interview_sessions', ['status'])
    op.create_index('ix_interview_questions_session_id', 'interview_questions', ['session_id'])
    op.create_index('ix_interview_feedback_session_id', 'interview_feedback', ['session_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_interview_feedback_session_id', table_name='interview_feedback')
    op.drop_index('ix_interview_questions_session_id', table_name='interview_questions')
    op.drop_index('ix_interview_sessions_status', table_name='interview_sessions')
    op.drop_index('ix_interview_sessions_resume_id', table_name='interview_sessions')
    op.drop_index('ix_interview_sessions_interviewer_id', table_name='interview_sessions')
    
    # Drop tables
    op.drop_table('interview_templates')
    op.drop_table('interview_feedback')
    op.drop_table('interview_questions')
    op.drop_table('interview_sessions')
    
    # Drop enum types if they exist
    op.execute("DROP TYPE IF EXISTS questioncategory")
    op.execute("DROP TYPE IF EXISTS interviewstatus")