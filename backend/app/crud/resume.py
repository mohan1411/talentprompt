"""Resume CRUD operations."""

from datetime import datetime
import logging
from typing import List, Optional, Union, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, func, extract, cast, Date
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
        """Get all resumes for a specific user, ordered by newest first."""
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .where(Resume.status != 'deleted')  # Exclude soft-deleted resumes
            .order_by(Resume.created_at.desc())
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
        """Soft delete a resume and remove its vector embeddings."""
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
            # Continue with soft delete even if vector deletion fails
        
        # Soft delete by setting status to 'deleted'
        resume.status = 'deleted'
        resume.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(resume)
        
        logger.info(f"Soft deleted resume {id} by setting status to 'deleted'")
        return resume
    
    async def hard_delete(self, db: AsyncSession, *, id: UUID) -> Resume:
        """Permanently delete a resume and its vector embeddings."""
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
            # Continue with hard delete even if vector deletion fails
        
        # Hard delete from database
        await db.delete(resume)
        await db.commit()
        
        logger.info(f"Hard deleted resume {id} from database")
        return resume
    
    async def get_upload_statistics(
        self,
        db: AsyncSession,
        *,
        aggregation: str = "daily",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get resume upload statistics grouped by date.
        
        Args:
            db: Database session
            aggregation: One of 'daily', 'weekly', 'monthly', 'yearly'
            start_date: Filter start date (optional)
            end_date: Filter end date (optional)
            user_id: Filter by specific user (optional)
        
        Returns:
            List of dictionaries with date and count
        """
        # Build base query
        query = select(Resume).where(Resume.status != 'deleted')
        
        # Apply date filters
        if start_date:
            query = query.where(Resume.created_at >= start_date)
        if end_date:
            query = query.where(Resume.created_at <= end_date)
        
        # Apply user filter if provided
        if user_id:
            query = query.where(Resume.user_id == user_id)
        
        # Apply aggregation based on type
        if aggregation == "yearly":
            # Group by year
            date_expr = extract('year', Resume.created_at).label('date')
            query = (
                select(
                    date_expr,
                    func.count(Resume.id).label('count')
                )
                .select_from(Resume)
                .where(Resume.status != 'deleted')
            )
            if start_date:
                query = query.where(Resume.created_at >= start_date)
            if end_date:
                query = query.where(Resume.created_at <= end_date)
            if user_id:
                query = query.where(Resume.user_id == user_id)
            query = query.group_by(date_expr).order_by(date_expr)
            
        elif aggregation == "monthly":
            # Group by year and month
            year_expr = extract('year', Resume.created_at)
            month_expr = extract('month', Resume.created_at)
            query = (
                select(
                    year_expr.label('year'),
                    month_expr.label('month'),
                    func.count(Resume.id).label('count')
                )
                .select_from(Resume)
                .where(Resume.status != 'deleted')
            )
            if start_date:
                query = query.where(Resume.created_at >= start_date)
            if end_date:
                query = query.where(Resume.created_at <= end_date)
            if user_id:
                query = query.where(Resume.user_id == user_id)
            query = query.group_by(year_expr, month_expr).order_by(year_expr, month_expr)
            
        elif aggregation == "weekly":
            # Group by year and week
            year_expr = extract('year', Resume.created_at)
            week_expr = extract('week', Resume.created_at)
            query = (
                select(
                    year_expr.label('year'),
                    week_expr.label('week'),
                    func.count(Resume.id).label('count')
                )
                .select_from(Resume)
                .where(Resume.status != 'deleted')
            )
            if start_date:
                query = query.where(Resume.created_at >= start_date)
            if end_date:
                query = query.where(Resume.created_at <= end_date)
            if user_id:
                query = query.where(Resume.user_id == user_id)
            query = query.group_by(year_expr, week_expr).order_by(year_expr, week_expr)
            
        else:  # daily
            # Group by date (cast to date to remove time)
            date_expr = cast(Resume.created_at, Date).label('date')
            query = (
                select(
                    date_expr,
                    func.count(Resume.id).label('count')
                )
                .select_from(Resume)
                .where(Resume.status != 'deleted')
            )
            if start_date:
                query = query.where(Resume.created_at >= start_date)
            if end_date:
                query = query.where(Resume.created_at <= end_date)
            if user_id:
                query = query.where(Resume.user_id == user_id)
            query = query.group_by(date_expr).order_by(date_expr)
        
        # Execute query
        result = await db.execute(query)
        rows = result.all()
        
        # Format results based on aggregation type
        statistics = []
        for row in rows:
            if aggregation == "yearly":
                statistics.append({
                    "date": str(int(row.date)),
                    "count": row.count
                })
            elif aggregation == "monthly":
                statistics.append({
                    "date": f"{int(row.year)}-{int(row.month):02d}",
                    "count": row.count
                })
            elif aggregation == "weekly":
                statistics.append({
                    "date": f"{int(row.year)}-W{int(row.week):02d}",
                    "count": row.count
                })
            else:  # daily
                statistics.append({
                    "date": row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date),
                    "count": row.count
                })
        
        return statistics


resume = CRUDResume(Resume)