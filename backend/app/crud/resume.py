"""Resume CRUD operations."""

from datetime import datetime
import logging
from typing import List, Optional, Union, Dict, Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.resume import Resume
from app.schemas.resume import ResumeCreate, ResumeUpdate
from app.services.reindex_service import reindex_service

logger = logging.getLogger(__name__)


class CRUDResume(CRUDBase[Resume, ResumeCreate, ResumeUpdate]):
    """CRUD operations for resumes."""
    
    async def create_with_user(
        self, db: AsyncSession, *, obj_in: ResumeCreate, user_id: UUID
    ) -> Resume:
        """Create a new resume for a user."""
        db_obj = Resume(
            user_id=user_id,
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            email=obj_in.email,
            phone=obj_in.phone,
            location=obj_in.location,
            summary=obj_in.summary,
            current_title=obj_in.current_title,
            years_experience=obj_in.years_experience,
            raw_text=obj_in.raw_text,
            original_filename=obj_in.original_filename,
            file_size=obj_in.file_size,
            file_type=obj_in.file_type,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_by_user(
        self, db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Resume]:
        """Get all resumes for a specific user."""
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_active_by_user(
        self, db: AsyncSession, *, user_id: UUID
    ) -> Optional[Resume]:
        """Get the active resume for a user."""
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .where(Resume.status == "active")
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def update_parse_status(
        self, db: AsyncSession, *, db_obj: Resume, status: str, parsed_data: Optional[dict] = None
    ) -> Resume:
        """Update resume parse status and data."""
        update_data = {
            "parse_status": status,
            "parsed_at": datetime.utcnow() if status == "completed" else None,
            "updated_at": datetime.utcnow()
        }
        
        needs_reindex = False
        
        if parsed_data:
            update_data["parsed_data"] = parsed_data
            # Extract skills and keywords if present
            if "skills" in parsed_data:
                update_data["skills"] = parsed_data["skills"]
                needs_reindex = True
            if "keywords" in parsed_data:
                update_data["keywords"] = parsed_data["keywords"]
                needs_reindex = True
        
        await db.execute(
            update(Resume)
            .where(Resume.id == db_obj.id)
            .values(**update_data)
        )
        await db.commit()
        await db.refresh(db_obj)
        
        # Re-index if skills or keywords were updated
        if needs_reindex:
            await reindex_service.reindex_resume(db, db_obj)
        
        return db_obj
    
    async def increment_view_count(
        self, db: AsyncSession, *, resume_id: UUID
    ) -> None:
        """Increment resume view count."""
        await db.execute(
            update(Resume)
            .where(Resume.id == resume_id)
            .values(view_count=Resume.view_count + 1)
        )
        await db.commit()
    
    async def increment_search_appearance(
        self, db: AsyncSession, *, resume_ids: List[UUID]
    ) -> None:
        """Increment search appearance count for multiple resumes."""
        if resume_ids:
            await db.execute(
                update(Resume)
                .where(Resume.id.in_(resume_ids))
                .values(search_appearance_count=Resume.search_appearance_count + 1)
            )
            await db.commit()
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Resume,
        obj_in: Union[ResumeUpdate, Dict[str, Any]]
    ) -> Resume:
        """Update a resume and re-index in vector search."""
        # Check if skills are being updated
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        # Track if we need to re-index
        needs_reindex = False
        reindex_fields = ['skills', 'summary', 'current_title', 'keywords', 'location']
        
        for field in reindex_fields:
            if field in update_data:
                needs_reindex = True
                break
        
        # Perform the update using parent class method
        updated_resume = await super().update(db, db_obj=db_obj, obj_in=obj_in)
        
        # Re-index in vector search if needed
        if needs_reindex:
            await reindex_service.reindex_resume(db, updated_resume)
        
        return updated_resume
    
    async def remove(self, db: AsyncSession, *, id: UUID) -> Resume:
        """Remove a resume and its vector embeddings."""
        # First get the resume to ensure it exists
        resume = await self.get(db, id=id)
        if not resume:
            return None
        
        # Delete from vector search
        try:
            from app.services.vector_search import vector_search
            await vector_search.delete_resume(str(id))
            logger.info(f"Deleted vector embeddings for resume {id}")
        except Exception as e:
            logger.error(f"Failed to delete vector embeddings for resume {id}: {e}")
            # Continue with database deletion even if vector deletion fails
        
        # Delete from database using parent method
        return await super().remove(db, id=id)


resume = CRUDResume(Resume)