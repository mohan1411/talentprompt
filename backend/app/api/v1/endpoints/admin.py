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