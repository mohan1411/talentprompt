"""Manually create outreach tables if they don't exist."""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

async def create_tables():
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found!")
        return
        
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(database_url)
    
    async with engine.connect() as conn:
        # Check if tables exist
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'outreach_messages'
            );
        """))
        
        if not result.scalar():
            print("Creating outreach tables...")
            
            # Create enum types if they don't exist
            await conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE messagestyle AS ENUM ('casual', 'professional', 'technical');
                EXCEPTION WHEN duplicate_object THEN null;
                END $$;
            """))
            
            await conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE messagestatus AS ENUM ('generated', 'sent', 'opened', 'responded', 'not_interested');
                EXCEPTION WHEN duplicate_object THEN null;
                END $$;
            """))
            
            # Create outreach_messages table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS outreach_messages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id),
                    resume_id UUID NOT NULL REFERENCES resumes(id),
                    subject VARCHAR(255) NOT NULL,
                    body TEXT NOT NULL,
                    style messagestyle NOT NULL,
                    job_title VARCHAR(255),
                    job_requirements JSON,
                    company_name VARCHAR(255),
                    status messagestatus DEFAULT 'generated',
                    sent_at TIMESTAMP,
                    opened_at TIMESTAMP,
                    responded_at TIMESTAMP,
                    quality_score FLOAT,
                    response_rate FLOAT,
                    generation_prompt TEXT,
                    model_version VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create indexes
            await conn.execute(text("CREATE INDEX idx_outreach_messages_user_id ON outreach_messages(user_id);"))
            await conn.execute(text("CREATE INDEX idx_outreach_messages_resume_id ON outreach_messages(resume_id);"))
            await conn.execute(text("CREATE INDEX idx_outreach_messages_status ON outreach_messages(status);"))
            await conn.execute(text("CREATE INDEX idx_outreach_messages_created_at ON outreach_messages(created_at);"))
            
            # Create outreach_templates table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS outreach_templates (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id),
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    subject_template VARCHAR(500),
                    body_template TEXT NOT NULL,
                    style messagestyle NOT NULL,
                    industry VARCHAR(100),
                    role_level VARCHAR(50),
                    job_function VARCHAR(100),
                    times_used INTEGER DEFAULT 0,
                    avg_response_rate FLOAT,
                    is_public BOOLEAN DEFAULT false,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create indexes for templates
            await conn.execute(text("CREATE INDEX idx_outreach_templates_user_id ON outreach_templates(user_id);"))
            await conn.execute(text("CREATE INDEX idx_outreach_templates_is_public ON outreach_templates(is_public);"))
            await conn.execute(text("CREATE INDEX idx_outreach_templates_style ON outreach_templates(style);"))
            
            await conn.commit()
            print("✅ Outreach tables created successfully!")
            
            # Update alembic version
            await conn.execute(text("DELETE FROM alembic_version WHERE version_num = 'add_outreach_tables';"))
            await conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('add_outreach_tables');"))
            await conn.commit()
            print("✅ Migration marked as complete!")
        else:
            print("✅ Outreach tables already exist!")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())