"""Bulk import endpoints for LinkedIn profiles."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api import deps
from app.models.user import User
from app.services.bulk_import import bulk_import_service
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class QueueProfileRequest(BaseModel):
    """Request to add profiles to import queue."""
    profiles: List[Dict[str, Any]] = Field(..., description="List of profile data to import")
    source: str = Field(default="manual", description="Import source")


class QueueStatusResponse(BaseModel):
    """Import queue status response."""
    status_counts: Dict[str, int]
    total: int
    is_processing: bool
    rate_limit_ok: bool
    rate_limits: Dict[str, Dict[str, int]]
    recent_items: List[Dict[str, Any]]


@router.post("/queue/add")
async def add_to_import_queue(
    request: QueueProfileRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Add profiles to the import queue."""
    
    logger.info(f"User {current_user.id} adding {len(request.profiles)} profiles to queue")
    
    # Validate profiles
    if len(request.profiles) > 100:
        raise HTTPException(
            status_code=400,
            detail="Cannot add more than 100 profiles at once"
        )
    
    # Add to queue
    result = await bulk_import_service.add_to_queue(
        db=db,
        user_id=current_user.id,
        profiles=request.profiles,
        source=request.source
    )
    
    return {
        "success": True,
        "result": result,
        "message": f"Added {result['added']} profiles to queue"
    }


@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> QueueStatusResponse:
    """Get import queue status for the current user."""
    
    status = await bulk_import_service.get_queue_status(db, current_user.id)
    return QueueStatusResponse(**status)


@router.post("/queue/process")
async def start_queue_processing(
    background_tasks: BackgroundTasks,
    max_items: Optional[int] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Start processing the import queue."""
    
    logger.info(f"User {current_user.id} starting queue processing")
    
    # Check rate limit first
    if not await bulk_import_service.rate_limiter.check_rate_limit(db, current_user.id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Start processing
    result = await bulk_import_service.process_queue(
        db=db,
        user_id=current_user.id,
        max_items=max_items
    )
    
    return result


@router.delete("/queue/clear")
async def clear_import_queue(
    status: Optional[str] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Clear import queue items."""
    
    if status and status not in ["pending", "failed"]:
        raise HTTPException(
            status_code=400,
            detail="Can only clear pending or failed items"
        )
    
    result = await bulk_import_service.clear_queue(
        db=db,
        user_id=current_user.id,
        status=status
    )
    
    return result


@router.post("/upload/linkedin-export")
async def upload_linkedin_export(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    request: Request = None
) -> Dict[str, Any]:
    """Upload and process LinkedIn export file (CSV, Excel, or ZIP)."""
    
    # Validate file
    allowed_extensions = ['.csv', '.xlsx', '.xls', '.zip']
    file_ext = '.' + file.filename.split('.')[-1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Check file size (50MB limit)
    if file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 50MB."
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Process the export file
        profiles = await bulk_import_service.export_processor.process_export_file(
            content, file.filename
        )
        
        if not profiles:
            raise HTTPException(
                status_code=400,
                detail="No valid profiles found in the uploaded file"
            )
        
        # Determine source based on file type
        source = "csv_upload"
        if file_ext in ['.xlsx', '.xls']:
            source = "excel_upload"
        elif file_ext == '.zip':
            source = "zip_archive"
        
        # Add profiles to queue
        result = await bulk_import_service.add_to_queue(
            db=db,
            user_id=current_user.id,
            profiles=profiles,
            source=source
        )
        
        # Track import for compliance
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            # Log import activity
            logger.info(f"User {current_user.id} uploaded {file.filename} from IP {ip_address}")
        
        return {
            "success": True,
            "filename": file.filename,
            "profiles_found": len(profiles),
            "result": result,
            "message": f"Successfully queued {result['added']} profiles for import"
        }
        
    except Exception as e:
        logger.error(f"Error processing LinkedIn export: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(e)}"
        )


@router.get("/stats")
async def get_import_statistics(
    days: int = 30,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Get import statistics for the current user."""
    
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=400,
            detail="Days must be between 1 and 365"
        )
    
    stats = await bulk_import_service.get_import_stats(
        db=db,
        user_id=current_user.id,
        days=days
    )
    
    return stats


@router.post("/webhook/linkedin")
async def receive_linkedin_webhook(
    payload: Dict[str, Any],
    api_key: str = Depends(deps.get_api_key),
    db: AsyncSession = Depends(deps.get_db)
) -> Dict[str, Any]:
    """Webhook endpoint for third-party LinkedIn integrations."""
    
    # Validate webhook payload
    if "profiles" not in payload or not isinstance(payload["profiles"], list):
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook payload. Expected 'profiles' array."
        )
    
    # Get user from API key
    user = await deps.get_user_from_api_key(db, api_key)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # Add profiles to queue
    result = await bulk_import_service.add_to_queue(
        db=db,
        user_id=user.id,
        profiles=payload["profiles"],
        source="webhook"
    )
    
    logger.info(f"Webhook import for user {user.id}: {result}")
    
    return {
        "success": True,
        "result": result,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/compliance/limits")
async def get_compliance_limits(
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """Get current rate limits and compliance information."""
    
    return {
        "rate_limits": bulk_import_service.rate_limiter.limits,
        "best_practices": [
            "Import profiles during normal browsing patterns",
            "Avoid importing more than 100 profiles per hour",
            "Use official LinkedIn exports when possible",
            "Respect profile privacy settings",
            "Maintain human-like delays between imports"
        ],
        "compliance_notice": (
            "This bulk import feature is designed to comply with LinkedIn's Terms of Service. "
            "All imports must be initiated by users with legitimate access to the profiles. "
            "Automated scraping or circumvention of access controls is prohibited."
        )
    }


@router.get("/compliance/report")
async def generate_compliance_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> Dict[str, Any]:
    """Generate compliance report for imports (admin only)."""
    
    # This would generate a detailed compliance report
    # showing import patterns, rate limit adherence, etc.
    
    return {
        "report_generated": datetime.utcnow().isoformat(),
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        },
        "message": "Compliance report generation not yet implemented"
    }