"""Service for re-indexing resumes in vector search."""

import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.resume import Resume
from app.services.vector_search import vector_search

logger = logging.getLogger(__name__)


class ReindexService:
    """Handle re-indexing of resumes in vector search."""
    
    async def reindex_resume(self, db: AsyncSession, resume: Resume) -> bool:
        """Re-index a single resume in vector search.
        
        Args:
            db: Database session
            resume: Resume object to re-index
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Build search text from resume data
            search_text = self._build_search_text(resume)
            
            # Build metadata
            metadata = {
                "name": f"{resume.first_name} {resume.last_name}",
                "title": resume.current_title,
                "location": resume.location,
                "skills": resume.skills or []
            }
            
            # Index in vector search
            logger.info(f"Re-indexing resume {resume.id} for {metadata['name']}")
            embedding = await vector_search.index_resume(
                resume_id=str(resume.id),
                text=search_text,
                metadata=metadata
            )
            
            # Update embedding in database if successful
            if embedding:
                resume.embedding = embedding
                await db.commit()
                logger.info(f"Successfully re-indexed resume {resume.id}")
                return True
            else:
                logger.warning(f"Failed to generate embedding for resume {resume.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error re-indexing resume {resume.id}: {e}")
            return False
    
    async def reindex_resume_by_id(self, db: AsyncSession, resume_id: UUID) -> bool:
        """Re-index a resume by ID.
        
        Args:
            db: Database session
            resume_id: Resume ID to re-index
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Fetch the resume
        stmt = select(Resume).where(Resume.id == resume_id)
        result = await db.execute(stmt)
        resume = result.scalar_one_or_none()
        
        if not resume:
            logger.error(f"Resume {resume_id} not found")
            return False
            
        return await self.reindex_resume(db, resume)
    
    async def reindex_multiple_resumes(self, db: AsyncSession, resume_ids: List[UUID]) -> dict:
        """Re-index multiple resumes.
        
        Args:
            db: Database session
            resume_ids: List of resume IDs to re-index
            
        Returns:
            dict: Results with success count and failed IDs
        """
        success_count = 0
        failed_ids = []
        
        for resume_id in resume_ids:
            if await self.reindex_resume_by_id(db, resume_id):
                success_count += 1
            else:
                failed_ids.append(str(resume_id))
        
        return {
            "total": len(resume_ids),
            "success": success_count,
            "failed": len(failed_ids),
            "failed_ids": failed_ids
        }
    
    async def reindex_all_resumes(self, db: AsyncSession, batch_size: int = 100) -> dict:
        """Re-index all active resumes.
        
        Args:
            db: Database session
            batch_size: Number of resumes to process at once
            
        Returns:
            dict: Results with total count and success count
        """
        # Get all active resumes
        stmt = select(Resume).where(Resume.status == 'active')
        result = await db.execute(stmt)
        resumes = result.scalars().all()
        
        total_count = len(resumes)
        success_count = 0
        
        # Process in batches
        for i in range(0, total_count, batch_size):
            batch = resumes[i:i + batch_size]
            for resume in batch:
                if await self.reindex_resume(db, resume):
                    success_count += 1
            
            logger.info(f"Re-indexed batch {i // batch_size + 1}: {i + len(batch)}/{total_count}")
        
        return {
            "total": total_count,
            "success": success_count,
            "failed": total_count - success_count
        }
    
    def _build_search_text(self, resume: Resume) -> str:
        """Build searchable text from resume data.
        
        Args:
            resume: Resume object
            
        Returns:
            str: Combined text for embedding
        """
        parts = []
        
        # Add name
        parts.append(f"{resume.first_name} {resume.last_name}")
        
        # Add current title
        if resume.current_title:
            parts.append(resume.current_title)
        
        # Add summary
        if resume.summary:
            parts.append(resume.summary)
        
        # Add skills
        if resume.skills:
            parts.append(f"Skills: {', '.join(resume.skills)}")
        
        # Add keywords
        if resume.keywords:
            parts.append(f"Keywords: {', '.join(resume.keywords)}")
        
        # Add location
        if resume.location:
            parts.append(f"Location: {resume.location}")
        
        # Add experience if available in parsed data
        if resume.parsed_data and isinstance(resume.parsed_data, dict):
            experience = resume.parsed_data.get('experience', [])
            for exp in experience[:3]:  # Include top 3 experiences
                if isinstance(exp, dict):
                    title = exp.get('title', '')
                    company = exp.get('company', '')
                    if title or company:
                        parts.append(f"{title} at {company}")
        
        return " ".join(parts)


# Create singleton instance
reindex_service = ReindexService()