"""Admin endpoints for system maintenance."""

import logging
from typing import Dict, Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api import deps
from app.models.user import User
from app.services.reindex_service import reindex_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ReindexRequest(BaseModel):
    """Request model for re-indexing resumes."""
    resume_ids: List[UUID]


class ReindexAllRequest(BaseModel):
    """Request model for re-indexing all resumes."""
    batch_size: int = 100


@router.post("/reindex-resume/{resume_id}", response_model=Dict[str, Any])
async def reindex_single_resume(
    resume_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """Re-index a single resume in vector search."""
    
    logger.info(f"Admin re-index requested for resume {resume_id} by user {current_user.id}")
    
    success = await reindex_service.reindex_resume_by_id(db, resume_id)
    
    if success:
        return {
            "success": True,
            "message": f"Successfully re-indexed resume {resume_id}"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to re-index resume {resume_id}"
        )


@router.post("/reindex-resumes", response_model=Dict[str, Any])
async def reindex_multiple_resumes(
    request: ReindexRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """Re-index multiple resumes in vector search."""
    
    logger.info(f"Admin re-index requested for {len(request.resume_ids)} resumes by user {current_user.id}")
    
    result = await reindex_service.reindex_multiple_resumes(db, request.resume_ids)
    
    return {
        "success": result["success"] > 0,
        "message": f"Re-indexed {result['success']} out of {result['total']} resumes",
        "details": result
    }


@router.post("/reindex-all", response_model=Dict[str, Any])
async def reindex_all_resumes(
    background_tasks: BackgroundTasks,
    request: ReindexAllRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Dict[str, Any]:
    """Re-index all resumes in vector search (superuser only)."""
    
    logger.info(f"Admin re-index ALL requested by superuser {current_user.id}")
    
    # Run in background to avoid timeout
    background_tasks.add_task(
        reindex_service.reindex_all_resumes,
        db,
        request.batch_size
    )
    
    return {
        "success": True,
        "message": "Re-indexing all resumes started in background",
        "batch_size": request.batch_size
    }


@router.get("/reindex-status", response_model=Dict[str, Any])
async def get_reindex_status(
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """Get current re-indexing status (placeholder for future implementation)."""
    
    return {
        "status": "idle",
        "message": "No active re-indexing operations",
        "last_reindex": None
    }


@router.post("/cleanup-orphaned-embeddings", response_model=Dict[str, Any])
async def cleanup_orphaned_embeddings(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """Clean up orphaned embeddings in vector search that don't have corresponding database records."""
    
    from app.services.vector_search import vector_search
    from app.models.resume import Resume
    from sqlalchemy import select
    
    logger.info("Starting orphaned embeddings cleanup")
    
    try:
        # Get all resume IDs from database
        stmt = select(Resume.id)
        result = await db.execute(stmt)
        db_resume_ids = {str(r) for r in result.scalars().all()}
        logger.info(f"Found {len(db_resume_ids)} resumes in database")
        
        # Get all points from Qdrant
        # Note: This is a simplified approach. In production, you might want to paginate
        from qdrant_client.models import Filter
        
        scroll_result = vector_search.client.scroll(
            collection_name=vector_search.collection_name,
            limit=1000,  # Adjust based on your data size
            with_payload=True,
            with_vectors=False
        )
        
        vector_ids = set()
        orphaned_ids = []
        
        if scroll_result and scroll_result[0]:
            for point in scroll_result[0]:
                point_id = str(point.id)
                vector_ids.add(point_id)
                
                # Check if this ID exists in database
                if point_id not in db_resume_ids:
                    orphaned_ids.append(point_id)
                    logger.info(f"Found orphaned embedding: {point_id}")
        
        logger.info(f"Found {len(vector_ids)} embeddings in vector search")
        logger.info(f"Found {len(orphaned_ids)} orphaned embeddings")
        
        # Delete orphaned embeddings
        deleted_count = 0
        for orphaned_id in orphaned_ids:
            try:
                await vector_search.delete_resume(orphaned_id)
                deleted_count += 1
                logger.info(f"Deleted orphaned embedding: {orphaned_id}")
            except Exception as e:
                logger.error(f"Failed to delete orphaned embedding {orphaned_id}: {e}")
        
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} orphaned embeddings",
            "details": {
                "total_db_resumes": len(db_resume_ids),
                "total_vector_embeddings": len(vector_ids),
                "orphaned_found": len(orphaned_ids),
                "orphaned_deleted": deleted_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error during orphaned embeddings cleanup: {e}")
        return {
            "success": False,
            "message": f"Cleanup failed: {str(e)}"
        }


@router.post("/security-reindex-vectors", response_model=Dict[str, Any])
async def security_reindex_vectors(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """
    CRITICAL SECURITY FIX: Re-index all vectors with user_id.
    
    This fixes the security issue where users could see all resumes.
    Only superusers or the initial admin can run this.
    """
    # Check if user is authorized
    if not current_user.is_superuser and current_user.email != "mohanarasu.chinnasamy@gmail.com":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can run this operation"
        )
    
    try:
        from app.services.vector_search import vector_search
        from app.services.embeddings import embedding_service
        from app.models.resume import Resume
        from sqlalchemy import select
        
        logger.info("Starting SECURITY re-indexing with user_id")
        
        # Get all resumes with completed parse status
        stmt = select(Resume).where(
            Resume.status == 'active',
            Resume.parse_status == 'completed'
        )
        
        result = await db.execute(stmt)
        resumes = result.scalars().all()
        
        logger.info(f"Found {len(resumes)} resumes to re-index for security")
        
        success_count = 0
        error_count = 0
        errors = []
        
        for resume in resumes:
            try:
                # Prepare resume text for embedding
                resume_data = {
                    "first_name": resume.first_name,
                    "last_name": resume.last_name,
                    "email": resume.email,
                    "phone": resume.phone,
                    "location": resume.location,
                    "current_title": resume.current_title,
                    "summary": resume.summary,
                    "years_experience": resume.years_experience,
                    "skills": resume.skills or [],
                    "keywords": resume.keywords or []
                }
                
                resume_text = embedding_service.prepare_resume_text(resume_data)
                
                # Prepare metadata with user_id - CRITICAL FOR SECURITY
                metadata = {
                    "user_id": str(resume.user_id),  # CRITICAL: Include user_id for security
                    "first_name": resume.first_name or "",
                    "last_name": resume.last_name or "",
                    "email": resume.email or "",
                    "location": resume.location or "",
                    "current_title": resume.current_title or "",
                    "years_experience": resume.years_experience or 0,
                    "skills": resume.skills or [],
                    "keywords": resume.keywords or []
                }
                
                # Re-index in Qdrant
                await vector_search.index_resume(
                    resume_id=str(resume.id),
                    text=resume_text,
                    metadata=metadata
                )
                
                success_count += 1
                logger.info(f"Re-indexed resume {resume.id} with user_id {resume.user_id}")
                
            except Exception as e:
                error_count += 1
                error_msg = f"Resume {resume.id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Failed to re-index {error_msg}")
        
        logger.info(f"Security re-indexing complete: {success_count} success, {error_count} errors")
        
        return {
            "status": "completed",
            "message": "Security re-indexing complete. Users can now only see their own resumes.",
            "total_resumes": len(resumes),
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[:10] if errors else []  # Return first 10 errors only
        }
        
    except Exception as e:
        logger.error(f"Critical error during security re-indexing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete security re-indexing: {str(e)}"
        )


@router.post("/cleanup-deleted-resumes", response_model=Dict[str, Any])
async def cleanup_deleted_resumes(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Dict[str, Any]:
    """Permanently delete all soft-deleted resumes and their embeddings (superuser only)."""
    
    from app.crud.resume import resume as resume_crud
    from sqlalchemy import select
    from app.models.resume import Resume
    
    logger.info("Starting cleanup of soft-deleted resumes")
    
    try:
        # Find all soft-deleted resumes
        stmt = select(Resume).where(Resume.status == 'deleted')
        result = await db.execute(stmt)
        deleted_resumes = result.scalars().all()
        
        logger.info(f"Found {len(deleted_resumes)} soft-deleted resumes")
        
        success_count = 0
        failed_ids = []
        
        for resume in deleted_resumes:
            try:
                await resume_crud.hard_delete(db, id=resume.id)
                success_count += 1
                logger.info(f"Hard deleted resume {resume.id}")
            except Exception as e:
                failed_ids.append(str(resume.id))
                logger.error(f"Failed to hard delete resume {resume.id}: {e}")
        
        return {
            "success": True,
            "message": f"Cleaned up {success_count} soft-deleted resumes",
            "details": {
                "total_found": len(deleted_resumes),
                "successfully_deleted": success_count,
                "failed": len(failed_ids),
                "failed_ids": failed_ids
            }
        }
        
    except Exception as e:
        logger.error(f"Error during deleted resumes cleanup: {e}")
        return {
            "success": False,
            "message": f"Cleanup failed: {str(e)}"
        }