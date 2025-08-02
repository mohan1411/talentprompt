#!/usr/bin/env python3
"""
Production migration script for Pipeline feature.
Executes SQL statements individually with proper error handling.
"""

import os
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def run_migration():
    # Get database URL
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment variables")
        return
    
    # Convert to asyncpg format
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "")
    elif DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "")
    
    print("📦 Connecting to production database...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(f"postgresql://{DATABASE_URL}")
        print("✅ Connected to database")
        
        # 1. Create base tables
        print("\n📋 Creating base tables...")
        
        # Users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                full_name VARCHAR(255),
                is_active BOOLEAN DEFAULT true,
                is_verified BOOLEAN DEFAULT false,
                role VARCHAR(50) DEFAULT 'user',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Users table")
        
        # Resumes table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                file_name VARCHAR(255) NOT NULL,
                file_path VARCHAR(500),
                file_size INTEGER,
                mime_type VARCHAR(100),
                parse_status VARCHAR(50) DEFAULT 'pending',
                parsed_data JSONB,
                vector_id VARCHAR(255),
                skills TEXT[],
                experience_years FLOAT,
                education_level VARCHAR(100),
                certifications TEXT[],
                languages TEXT[],
                location VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Resumes table")
        
        # Candidates table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                email VARCHAR(255),
                phone VARCHAR(50),
                current_title VARCHAR(255),
                current_company VARCHAR(255),
                years_of_experience FLOAT,
                skills TEXT[],
                education JSONB,
                experience JSONB,
                location VARCHAR(255),
                linkedin_url VARCHAR(500),
                github_url VARCHAR(500),
                portfolio_url VARCHAR(500),
                availability VARCHAR(100),
                salary_expectation VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Candidates table")
        
        # Create unique index on candidates email
        try:
            await conn.execute("""
                CREATE UNIQUE INDEX idx_candidates_email ON candidates(email) WHERE email IS NOT NULL
            """)
        except:
            pass  # Index might already exist
        
        # Jobs table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(255) NOT NULL,
                description TEXT,
                requirements TEXT[],
                nice_to_have TEXT[],
                department VARCHAR(100),
                location VARCHAR(255),
                employment_type VARCHAR(50),
                salary_range VARCHAR(100),
                is_active BOOLEAN DEFAULT true,
                created_by UUID REFERENCES users(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Jobs table")
        
        # Interview sessions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS interview_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
                job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
                interviewer_id UUID REFERENCES users(id),
                scheduled_at TIMESTAMP WITH TIME ZONE,
                duration_minutes INTEGER DEFAULT 60,
                meeting_link VARCHAR(500),
                status VARCHAR(50) DEFAULT 'scheduled',
                interview_type VARCHAR(50),
                interview_round INTEGER DEFAULT 1,
                notes TEXT,
                feedback JSONB,
                overall_rating NUMERIC(2,1),
                recommendation VARCHAR(50),
                started_at TIMESTAMP WITH TIME ZONE,
                ended_at TIMESTAMP WITH TIME ZONE,
                is_transcription_enabled BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Interview sessions table")
        
        # Interview questions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS interview_questions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
                question TEXT NOT NULL,
                question_type VARCHAR(50),
                expected_answer TEXT,
                candidate_response TEXT,
                response_rating INTEGER CHECK (response_rating >= 1 AND response_rating <= 5),
                notes TEXT,
                asked_at TIMESTAMP WITH TIME ZONE,
                time_taken_seconds INTEGER,
                order_index INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Interview questions table")
        
        # Transcriptions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transcriptions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
                content TEXT,
                speaker VARCHAR(100),
                timestamp_start FLOAT,
                timestamp_end FLOAT,
                confidence FLOAT,
                is_final BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Transcriptions table")
        
        # 2. Create enum types
        print("\n🔧 Creating enum types...")
        
        try:
            await conn.execute("""
                CREATE TYPE pipeline_stage_type AS ENUM (
                    'applied', 'screening', 'interview', 'offer', 
                    'hired', 'rejected', 'withdrawn'
                )
            """)
            print("  ✓ pipeline_stage_type enum")
        except Exception as e:
            if "already exists" in str(e):
                print("  ⏭ pipeline_stage_type enum already exists")
            else:
                raise
        
        try:
            await conn.execute("""
                CREATE TYPE pipeline_activity_type AS ENUM (
                    'moved', 'noted', 'assigned', 'tagged', 'contacted', 'evaluated'
                )
            """)
            print("  ✓ pipeline_activity_type enum")
        except Exception as e:
            if "already exists" in str(e):
                print("  ⏭ pipeline_activity_type enum already exists")
            else:
                raise
        
        # 3. Create pipeline tables
        print("\n📊 Creating pipeline tables...")
        
        # Pipelines table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pipelines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                stages JSONB NOT NULL DEFAULT '[]',
                is_active BOOLEAN DEFAULT true,
                is_default BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by UUID REFERENCES users(id)
            )
        """)
        print("  ✓ Pipelines table")
        
        # Add unique constraint for default pipeline
        try:
            await conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS only_one_default_pipeline 
                ON pipelines (is_default) 
                WHERE is_default = true
            """)
            print("  ✓ Default pipeline constraint")
        except Exception as e:
            if "already exists" in str(e):
                print("  ⏭ Default pipeline constraint already exists")
            else:
                print(f"  ⚠️ Default pipeline constraint: {e}")
        
        # Candidate pipeline states table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS candidate_pipeline_states (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
                pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
                current_stage VARCHAR(50) NOT NULL,
                stage_entered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                assigned_to UUID REFERENCES users(id),
                tags TEXT[] DEFAULT '{}',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(candidate_id, pipeline_id)
            )
        """)
        print("  ✓ Candidate pipeline states table")
        
        # Pipeline activities table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_activities (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                pipeline_state_id UUID NOT NULL REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
                activity_type pipeline_activity_type NOT NULL,
                from_stage VARCHAR(50),
                to_stage VARCHAR(50),
                performed_by UUID REFERENCES users(id),
                details JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Pipeline activities table")
        
        # Candidate notes table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS candidate_notes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                pipeline_state_id UUID NOT NULL REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
                note TEXT NOT NULL,
                is_private BOOLEAN DEFAULT false,
                created_by UUID REFERENCES users(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Candidate notes table")
        
        # Candidate evaluations table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS candidate_evaluations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                pipeline_state_id UUID NOT NULL REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
                interview_session_id UUID REFERENCES interview_sessions(id),
                evaluator_id UUID REFERENCES users(id),
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                strengths TEXT[],
                weaknesses TEXT[],
                recommendation VARCHAR(50),
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Candidate evaluations table")
        
        # Candidate communications table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS candidate_communications (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                pipeline_state_id UUID NOT NULL REFERENCES candidate_pipeline_states(id) ON DELETE CASCADE,
                communication_type VARCHAR(50) NOT NULL,
                subject VARCHAR(255),
                content TEXT,
                sent_at TIMESTAMP WITH TIME ZONE,
                sent_by UUID REFERENCES users(id),
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Candidate communications table")
        
        # Pipeline automations table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_automations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                trigger_stage VARCHAR(50),
                trigger_condition JSONB,
                action_type VARCHAR(50) NOT NULL,
                action_config JSONB,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Pipeline automations table")
        
        # Pipeline team members table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_team_members (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role VARCHAR(50) NOT NULL DEFAULT 'member',
                permissions JSONB DEFAULT '{}',
                added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                added_by UUID REFERENCES users(id),
                UNIQUE(pipeline_id, user_id)
            )
        """)
        print("  ✓ Pipeline team members table")
        
        # 4. Create indexes
        print("\n📑 Creating indexes...")
        
        indexes = [
            ("idx_resumes_user_id", "resumes(user_id)"),
            ("idx_resumes_parse_status", "resumes(parse_status)"),
            ("idx_candidates_resume_id", "candidates(resume_id)"),
            ("idx_interview_sessions_candidate", "interview_sessions(candidate_id)"),
            ("idx_interview_sessions_status", "interview_sessions(status)"),
            ("idx_interview_questions_session", "interview_questions(session_id)"),
            ("idx_pipeline_states_candidate", "candidate_pipeline_states(candidate_id)"),
            ("idx_pipeline_states_pipeline", "candidate_pipeline_states(pipeline_id)"),
            ("idx_pipeline_states_stage", "candidate_pipeline_states(current_stage)"),
            ("idx_pipeline_states_assigned", "candidate_pipeline_states(assigned_to)"),
            ("idx_pipeline_activities_state", "pipeline_activities(pipeline_state_id)"),
            ("idx_pipeline_activities_type", "pipeline_activities(activity_type)"),
        ]
        
        for idx_name, idx_def in indexes:
            try:
                await conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
                print(f"  ✓ {idx_name}")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"  ⏭ {idx_name} already exists")
                else:
                    print(f"  ⚠️ {idx_name}: {e}")
        
        # 5. Add pipeline support to interviews
        print("\n🔗 Adding pipeline support to interviews...")
        
        try:
            await conn.execute("""
                ALTER TABLE interview_sessions 
                ADD COLUMN pipeline_state_id UUID REFERENCES candidate_pipeline_states(id)
            """)
            print("  ✓ Added pipeline_state_id column")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e).lower():
                print("  ⏭ pipeline_state_id column already exists")
            else:
                raise
        
        # 6. Create default pipeline
        print("\n🎯 Creating default pipeline...")
        
        default_pipeline_stages = """[
            {
                "id": "applied",
                "name": "Applied",
                "description": "New applications",
                "color": "#6B7280",
                "order": 1,
                "is_terminal": false
            },
            {
                "id": "screening",
                "name": "Screening",
                "description": "Initial review and screening",
                "color": "#3B82F6",
                "order": 2,
                "is_terminal": false
            },
            {
                "id": "interview",
                "name": "Interview",
                "description": "Interview process",
                "color": "#8B5CF6",
                "order": 3,
                "is_terminal": false
            },
            {
                "id": "offer",
                "name": "Offer",
                "description": "Offer extended",
                "color": "#F59E0B",
                "order": 4,
                "is_terminal": false
            },
            {
                "id": "hired",
                "name": "Hired",
                "description": "Successfully hired",
                "color": "#10B981",
                "order": 5,
                "is_terminal": false
            },
            {
                "id": "rejected",
                "name": "Rejected",
                "description": "Not selected for position",
                "color": "#EF4444",
                "order": 6,
                "is_terminal": true
            },
            {
                "id": "withdrawn",
                "name": "Withdrawn",
                "description": "Candidate withdrew from process",
                "color": "#6B7280",
                "order": 7,
                "is_terminal": true
            }
        ]"""
        
        try:
            # Check if default pipeline already exists
            existing = await conn.fetchval("SELECT COUNT(*) FROM pipelines WHERE is_default = true")
            if existing == 0:
                await conn.execute("""
                    INSERT INTO pipelines (name, description, stages, is_active, is_default)
                    VALUES ($1, $2, $3::jsonb, $4, $5)
                """, 
                'Default Hiring Pipeline',
                'Standard recruitment workflow with all stages including terminal states',
                default_pipeline_stages,
                True,
                True)
                print("  ✓ Default pipeline created")
            else:
                print("  ⏭ Default pipeline already exists")
        except Exception as e:
            print(f"  ⚠️ Default pipeline: {e}")
        
        # 7. Create trigger function
        print("\n⚡ Creating trigger for automatic stage transitions...")
        
        await conn.execute("""
            CREATE OR REPLACE FUNCTION update_pipeline_stage_on_interview()
            RETURNS TRIGGER AS $$
            DECLARE
                v_pipeline_state_id UUID;
            BEGIN
                -- Only proceed if status is changing to 'scheduled'
                IF NEW.status = 'scheduled' AND (OLD.status IS NULL OR OLD.status != 'scheduled') THEN
                    -- Get the pipeline_state_id
                    v_pipeline_state_id := NEW.pipeline_state_id;
                    
                    IF v_pipeline_state_id IS NOT NULL THEN
                        -- Update the candidate's stage to 'interview'
                        UPDATE candidate_pipeline_states
                        SET current_stage = 'interview',
                            stage_entered_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = v_pipeline_state_id;
                        
                        -- Log the activity
                        INSERT INTO pipeline_activities (
                            pipeline_state_id,
                            activity_type,
                            from_stage,
                            to_stage,
                            details,
                            created_at
                        )
                        SELECT 
                            v_pipeline_state_id,
                            'moved'::pipeline_activity_type,
                            current_stage,
                            'interview',
                            jsonb_build_object(
                                'reason', 'Interview scheduled',
                                'automated', true,
                                'interview_id', NEW.id
                            ),
                            CURRENT_TIMESTAMP
                        FROM candidate_pipeline_states
                        WHERE id = v_pipeline_state_id;
                    END IF;
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """)
        print("  ✓ Trigger function created")
        
        # Drop and recreate trigger
        await conn.execute("DROP TRIGGER IF EXISTS interview_scheduled_pipeline_update ON interview_sessions")
        await conn.execute("""
            CREATE TRIGGER interview_scheduled_pipeline_update
            AFTER INSERT OR UPDATE ON interview_sessions
            FOR EACH ROW
            EXECUTE FUNCTION update_pipeline_stage_on_interview()
        """)
        print("  ✓ Trigger created")
        
        # 8. Verify migration
        print("\n✅ Verifying migration...")
        
        # Check tables
        result = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('pipelines', 'candidate_pipeline_states', 'pipeline_activities')
        """)
        print(f"  • Pipeline tables created: {result}/3")
        
        # Check default pipeline
        result = await conn.fetchval("""
            SELECT COUNT(*) FROM pipelines WHERE is_default = true
        """)
        print(f"  • Default pipeline exists: {'Yes' if result > 0 else 'No'}")
        
        # Check if we have candidates
        result = await conn.fetchval("SELECT COUNT(*) FROM candidates")
        print(f"  • Total candidates in database: {result}")
        
        # Check candidates in pipeline
        result = await conn.fetchval("SELECT COUNT(*) FROM candidate_pipeline_states")
        print(f"  • Candidates in pipeline: {result}")
        
        print("\n✨ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            await conn.close()
            print("\n🔒 Database connection closed")

if __name__ == "__main__":
    print("🚀 Pipeline Feature Production Migration")
    print("=" * 50)
    asyncio.run(run_migration())