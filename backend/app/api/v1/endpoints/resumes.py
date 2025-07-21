"""Resume endpoints."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.services.file_parser import FileParser
from app.services.resume_processor import resume_processor


class BulkDeleteRequest(BaseModel):
    """Request schema for bulk delete."""
    resume_ids: List[UUID]


class BulkUpdatePositionRequest(BaseModel):
    """Request schema for bulk update position."""
    resume_ids: List[UUID]
    job_position: str

router = APIRouter()


@router.post("/", response_model=schemas.Resume)
async def upload_resume(
    *,
    db: AsyncSession = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_position: str | None = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> schemas.Resume:
    """Upload a new resume."""
    # Validate file
    file_content = await file.read()
    file_size = len(file_content)
    
    is_valid, error_msg = FileParser.validate_file(file.filename, file_size)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Extract text from file
    try:
        text = FileParser.extract_text(file_content, file.filename)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Parse basic information from text (simple extraction for now)
    # TODO: Implement AI-powered parsing
    lines = text.split('\n')
    first_line_parts = lines[0].split() if lines else []
    
    resume_in = schemas.ResumeCreate(
        first_name=first_line_parts[0] if len(first_line_parts) > 0 else "Unknown",
        last_name=first_line_parts[1] if len(first_line_parts) > 1 else "Unknown",
        raw_text=text,
        original_filename=file.filename,
        file_size=file_size,
        file_type=file.content_type or "application/octet-stream",
        job_position=job_position
    )
    
    # Check if user already has an active resume and deactivate it
    existing_resume = await crud.resume.get_active_by_user(db, user_id=current_user.id)
    if existing_resume:
        await crud.resume.update(
            db, db_obj=existing_resume, obj_in={"status": "inactive"}
        )
    
    # Create new resume
    resume = await crud.resume.create_with_user(
        db, obj_in=resume_in, user_id=current_user.id
    )
    
    # Queue background processing (parsing and embedding generation)
    if settings.OPENAI_API_KEY:
        background_tasks.add_task(
            resume_processor.process_resume_background,
            str(resume.id)
        )
    
    return resume


@router.get("/", response_model=List[schemas.Resume])
async def get_my_resumes(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> List[schemas.Resume]:
    """Get all resumes for the current user."""
    resumes = await crud.resume.get_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return resumes


@router.get("/{resume_id}", response_model=schemas.Resume)
async def get_resume(
    *,
    db: AsyncSession = Depends(deps.get_db),
    resume_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> schemas.Resume:
    """Get a specific resume."""
    resume = await crud.resume.get(db, id=resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Check ownership
    if resume.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Increment view count
    await crud.resume.increment_view_count(db, resume_id=resume_id)
    
    return resume


@router.put("/{resume_id}", response_model=schemas.Resume)
async def update_resume(
    *,
    db: AsyncSession = Depends(deps.get_db),
    resume_id: UUID,
    resume_in: schemas.ResumeUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> schemas.Resume:
    """Update a resume."""
    resume = await crud.resume.get(db, id=resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Check ownership
    if resume.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    resume = await crud.resume.update(db, db_obj=resume, obj_in=resume_in)
    return resume


@router.delete("/{resume_id}")
async def delete_resume(
    *,
    db: AsyncSession = Depends(deps.get_db),
    resume_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> dict:
    """Delete a resume."""
    resume = await crud.resume.get(db, id=resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Check ownership
    if resume.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    await crud.resume.remove(db, id=resume_id)
    return {"message": "Resume deleted successfully"}


@router.post("/bulk/delete", response_model=dict)
async def bulk_delete_resumes(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: BulkDeleteRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> dict:
    """Delete multiple resumes."""
    deleted_count = 0
    errors = []
    
    for resume_id in request.resume_ids:
        try:
            resume = await crud.resume.get(db, id=resume_id)
            if resume and resume.user_id == current_user.id:
                await crud.resume.remove(db, id=resume_id)
                deleted_count += 1
        except Exception as e:
            errors.append(f"Failed to delete resume {resume_id}: {str(e)}")
    
    response = {"message": f"Successfully deleted {deleted_count} resume(s)"}
    if errors:
        response["errors"] = errors
    
    return response


@router.post("/bulk/update-position", response_model=dict)
async def bulk_update_position(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request: BulkUpdatePositionRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> dict:
    """Update job position for multiple resumes."""
    updated_count = 0
    errors = []
    
    for resume_id in request.resume_ids:
        try:
            resume = await crud.resume.get(db, id=resume_id)
            if resume and resume.user_id == current_user.id:
                await crud.resume.update(
                    db, db_obj=resume, obj_in={"job_position": request.job_position}
                )
                updated_count += 1
        except Exception as e:
            errors.append(f"Failed to update resume {resume_id}: {str(e)}")
    
    response = {"message": f"Successfully updated {updated_count} resume(s)"}
    if errors:
        response["errors"] = errors
    
    return response


@router.get("/statistics", response_model=schemas.ResumeStatistics)
async def get_resume_statistics(
    *,
    db: AsyncSession = Depends(deps.get_db),
    aggregation: str = Query("daily", regex="^(daily|weekly|monthly|yearly)$"),
    start_date: Optional[datetime] = Query(None, description="Filter start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter end date (ISO format)"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> schemas.ResumeStatistics:
    """Get resume upload statistics grouped by date.
    
    Returns data suitable for bar charts with counts grouped by:
    - daily: Each day (YYYY-MM-DD)
    - weekly: Each week (YYYY-WW)
    - monthly: Each month (YYYY-MM)
    - yearly: Each year (YYYY)
    
    Admin users get statistics for all resumes.
    Regular users get statistics only for their own resumes.
    """
    # Determine if we should filter by user
    user_id = None if current_user.is_superuser else current_user.id
    
    # Get statistics from database
    statistics_data = await crud.resume.get_upload_statistics(
        db,
        aggregation=aggregation,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id
    )
    
    # Calculate total count
    total_count = sum(item["count"] for item in statistics_data)
    
    # Determine date range
    if statistics_data:
        dates = [item["date"] for item in statistics_data]
        start_date_str = min(dates)
        end_date_str = max(dates)
    else:
        start_date_str = start_date.isoformat() if start_date else ""
        end_date_str = end_date.isoformat() if end_date else ""
    
    # Convert to response schema
    return schemas.ResumeStatistics(
        aggregation=aggregation,
        data=[
            schemas.ResumeStatisticsItem(date=item["date"], count=item["count"])
            for item in statistics_data
        ],
        total_count=total_count,
        start_date=start_date_str,
        end_date=end_date_str
    )