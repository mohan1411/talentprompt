"""Create missing tables on startup."""

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def ensure_submission_tables(db: AsyncSession):
    """Create submission tables if they don't exist."""
    try:
        # Check if tables exist
        result = await db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name IN ('candidate_submissions', 'invitation_campaigns')
        """))
        
        count = result.scalar()
        
        if count < 2:
            logger.warning("Creating missing submission tables...")
            
            # Create tables
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS invitation_campaigns (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    recruiter_id UUID NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    source_type VARCHAR(50),
                    source_data JSONB,
                    is_public BOOLEAN DEFAULT FALSE,
                    public_slug VARCHAR(100),
                    email_template TEXT,
                    expires_in_days INTEGER DEFAULT 7,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS candidate_submissions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    token VARCHAR(255) UNIQUE NOT NULL,
                    submission_type VARCHAR(10) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                    recruiter_id UUID NOT NULL,
                    campaign_id UUID,
                    resume_id UUID,
                    email VARCHAR(255) NOT NULL,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    phone VARCHAR(50),
                    linkedin_url VARCHAR(255),
                    availability VARCHAR(50),
                    salary_expectations JSONB,
                    location_preferences JSONB,
                    resume_text TEXT,
                    parsed_data JSONB,
                    email_sent_at TIMESTAMP,
                    email_opened_at TIMESTAMP,
                    link_clicked_at TIMESTAMP,
                    submitted_at TIMESTAMP,
                    processed_at TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await db.commit()
            logger.info("✅ Submission tables created successfully!")
            
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        await db.rollback()