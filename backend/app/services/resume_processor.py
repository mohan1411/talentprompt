"""Resume processing service for background tasks."""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app import crud
from app.models.resume import Resume
from app.services.embeddings import embedding_service
from app.services.resume_parser import resume_parser
from app.services.vector_search import vector_search
from app.core.config import settings

logger = logging.getLogger(__name__)


class ResumeProcessor:
    """Service for processing resumes (parsing and embedding generation)."""
    
    def __init__(self):
        """Initialize the processor with database engine."""
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=5,  # Smaller pool for background tasks
            max_overflow=5,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def process_resume_background(self, resume_id: str) -> bool:
        """Process a resume in background with its own database session."""
        async with self.async_session() as db:
            try:
                return await self.process_resume(db, resume_id)
            finally:
                await db.close()
    
    async def process_resume(self, db: AsyncSession, resume_id: str) -> bool:
        """Process a resume by parsing and generating embeddings.
        
        Args:
            db: Database session
            resume_id: ID of the resume to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the resume
            resume = await crud.resume.get(db, id=resume_id)
            if not resume:
                logger.error(f"Resume {resume_id} not found")
                return False
            
            # Update status to processing
            await crud.resume.update_parse_status(
                db, db_obj=resume, status="processing"
            )
            
            # Parse the resume
            if resume.raw_text:
                logger.info(f"Parsing resume {resume_id}")
                parsed_data = await resume_parser.parse_resume(resume.raw_text)
                
                # Update resume with parsed data
                update_data = {
                    "first_name": parsed_data.get("first_name", resume.first_name),
                    "last_name": parsed_data.get("last_name", resume.last_name),
                    "email": parsed_data.get("email") or resume.email,
                    "phone": parsed_data.get("phone") or resume.phone,
                    "location": parsed_data.get("location") or resume.location,
                    "current_title": parsed_data.get("current_title") or resume.current_title,
                    "summary": parsed_data.get("summary") or resume.summary,
                    "years_experience": parsed_data.get("years_experience") or resume.years_experience,
                    "skills": parsed_data.get("skills", []),
                    "keywords": parsed_data.get("keywords", [])
                }
                
                # Generate embedding
                logger.info(f"Generating embedding for resume {resume_id}")
                resume_text = embedding_service.prepare_resume_text(update_data)
                embedding = await embedding_service.generate_embedding(resume_text)
                
                if embedding:
                    # Update resume with parsed data and mark as completed
                    await crud.resume.update(db, db_obj=resume, obj_in=update_data)
                    
                    # Store embedding in database as JSON
                    await self._update_embedding(db, resume_id, embedding)
                    
                    # Index in Qdrant for vector search
                    metadata = {
                        "first_name": update_data.get("first_name", ""),
                        "last_name": update_data.get("last_name", ""),
                        "email": update_data.get("email", ""),
                        "location": update_data.get("location", ""),
                        "current_title": update_data.get("current_title", ""),
                        "years_experience": update_data.get("years_experience", 0),
                        "skills": update_data.get("skills", []),
                        "keywords": update_data.get("keywords", [])
                    }
                    
                    try:
                        await vector_search.index_resume(
                            resume_id=resume_id,
                            text=resume_text,
                            metadata=metadata
                        )
                        logger.info(f"Indexed resume {resume_id} in Qdrant")
                    except Exception as e:
                        logger.error(f"Failed to index resume {resume_id} in Qdrant: {e}")
                        # Don't fail the whole process if Qdrant indexing fails
                    
                    # Update parse status
                    await crud.resume.update_parse_status(
                        db, 
                        db_obj=resume, 
                        status="completed",
                        parsed_data=parsed_data
                    )
                    
                    logger.info(f"Successfully processed resume {resume_id}")
                    return True
                else:
                    raise Exception("Failed to generate embedding")
                    
            else:
                logger.warning(f"Resume {resume_id} has no raw text")
                await crud.resume.update_parse_status(
                    db, db_obj=resume, status="failed"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error processing resume {resume_id}: {e}")
            
            # Update status to failed
            try:
                resume = await crud.resume.get(db, id=resume_id)
                if resume:
                    await crud.resume.update_parse_status(
                        db, db_obj=resume, status="failed"
                    )
            except:
                pass
                
            return False
    
    async def _update_embedding(
        self, db: AsyncSession, resume_id: str, embedding: list
    ) -> None:
        """Update resume embedding using raw SQL to handle pgvector type."""
        from sqlalchemy import update
        from app.models.resume import Resume
        
        # Update using SQLAlchemy ORM
        stmt = (
            update(Resume)
            .where(Resume.id == resume_id)
            .values(embedding=embedding)
        )
        
        await db.execute(stmt)
        await db.commit()


# Singleton instance
resume_processor = ResumeProcessor()