"""Cleanup endpoints for fixing data issues."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import logging

from app import crud, models
from app.api import deps
from app.models.resume import Resume
from app.services.vector_search import vector_search

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/cleanup/orphaned-vectors")
async def cleanup_orphaned_vectors(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
):
    """Remove vector embeddings for resumes that no longer exist in the database."""
    try:
        # Get all resume IDs from the database
        result = await db.execute(select(Resume.id))
        db_resume_ids = {str(row[0]) for row in result}
        
        # Get all IDs from vector search
        vector_ids = await vector_search.get_all_ids()
        
        # Find orphaned vectors
        orphaned_ids = vector_ids - db_resume_ids
        
        # Delete orphaned vectors
        deleted_count = 0
        for resume_id in orphaned_ids:
            try:
                await vector_search.delete_resume(resume_id)
                deleted_count += 1
                logger.info(f"Deleted orphaned vector for resume {resume_id}")
            except Exception as e:
                logger.error(f"Failed to delete orphaned vector {resume_id}: {e}")
        
        return {
            "message": "Orphaned vectors cleanup completed",
            "total_vectors": len(vector_ids),
            "db_resumes": len(db_resume_ids),
            "orphaned_vectors": len(orphaned_ids),
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Failed to cleanup orphaned vectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/soft-deleted-resumes")
async def cleanup_soft_deleted_resumes(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
):
    """Permanently delete all soft-deleted resumes."""
    try:
        # Find all soft-deleted resumes
        result = await db.execute(
            select(Resume).where(Resume.status == 'deleted')
        )
        soft_deleted_resumes = result.scalars().all()
        
        deleted_count = 0
        vector_delete_count = 0
        
        for resume in soft_deleted_resumes:
            # Delete from vector search
            try:
                await vector_search.delete_resume(str(resume.id))
                vector_delete_count += 1
            except Exception as e:
                logger.error(f"Failed to delete vector for resume {resume.id}: {e}")
            
            # Hard delete from database
            await db.delete(resume)
            deleted_count += 1
        
        await db.commit()
        
        return {
            "message": "Soft-deleted resumes cleanup completed",
            "deleted_resumes": deleted_count,
            "deleted_vectors": vector_delete_count
        }
    except Exception as e:
        logger.error(f"Failed to cleanup soft-deleted resumes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cleanup/check-duplicates")
async def check_duplicate_resumes(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
):
    """Check for duplicate resumes by LinkedIn URL."""
    try:
        # Get all resumes with LinkedIn URLs
        result = await db.execute(
            select(Resume)
            .where(Resume.linkedin_url.isnot(None))
            .where(Resume.status != 'deleted')
            .order_by(Resume.linkedin_url, Resume.created_at)
        )
        resumes = result.scalars().all()
        
        # Group by LinkedIn URL
        url_groups = {}
        for resume in resumes:
            url = resume.linkedin_url.split('?')[0]  # Remove query params
            if url not in url_groups:
                url_groups[url] = []
            url_groups[url].append({
                'id': str(resume.id),
                'name': f"{resume.first_name} {resume.last_name}",
                'created_at': resume.created_at.isoformat(),
                'status': resume.status
            })
        
        # Find duplicates
        duplicates = {url: resumes for url, resumes in url_groups.items() if len(resumes) > 1}
        
        return {
            "total_resumes": len(resumes),
            "unique_profiles": len(url_groups),
            "duplicate_groups": len(duplicates),
            "duplicates": duplicates
        }
    except Exception as e:
        logger.error(f"Failed to check duplicates: {e}")
        raise HTTPException(status_code=500, detail=str(e))