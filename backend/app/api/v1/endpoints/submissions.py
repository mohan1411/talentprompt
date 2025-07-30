"""API endpoints for candidate submissions."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionResponse,
    SubmissionPublicResponse,
    SubmissionSubmit,
    CampaignCreate,
    CampaignResponse,
    CampaignPublicResponse,
    CampaignUpdate,
    BulkInviteRequest,
    BulkInviteResponse,
    SubmissionAnalytics,
    CampaignAnalytics
)
from app.services.submission_service import submission_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# Authenticated endpoints (for recruiters)
@router.post("/", response_model=SubmissionResponse)
async def create_submission(
    data: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new submission invitation."""
    import sys
    print(f"\n[API ENDPOINT] Creating submission for email: {data.email}", flush=True)
    print(f"[API ENDPOINT] Submission type: {data.submission_type}", flush=True)
    sys.stdout.flush()
    
    try:
        submission = await submission_service.create_submission(
            db=db,
            recruiter_id=current_user.id,
            data=data
        )
        print(f"[API ENDPOINT] Submission created successfully with ID: {submission.id}", flush=True)
        sys.stdout.flush()
        return submission
    except Exception as e:
        logger.error(f"Error creating submission: {e}")
        print(f"[API ENDPOINT] Error creating submission: {e}", flush=True)
        sys.stdout.flush()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create submission"
        )


@router.post("/bulk", response_model=BulkInviteResponse)
async def create_bulk_submissions(
    data: BulkInviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create bulk submission invitations."""
    try:
        result = await submission_service.create_bulk_submissions(
            db=db,
            recruiter_id=current_user.id,
            emails=data.emails,
            submission_type=data.submission_type,
            campaign_id=data.campaign_id,
            expires_in_days=data.expires_in_days
        )
        return result
    except Exception as e:
        logger.error(f"Error creating bulk submissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bulk submissions"
        )


@router.get("/", response_model=List[SubmissionResponse])
async def get_my_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    campaign_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all submissions for the current recruiter."""
    from sqlalchemy import select, and_
    from app.models.submission import CandidateSubmission, SubmissionStatus
    
    query = select(CandidateSubmission).where(
        CandidateSubmission.recruiter_id == current_user.id
    )
    
    if status:
        try:
            status_enum = SubmissionStatus(status)
            query = query.where(CandidateSubmission.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )
    
    if campaign_id:
        query = query.where(CandidateSubmission.campaign_id == campaign_id)
    
    query = query.order_by(CandidateSubmission.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    submissions = result.scalars().all()
    
    return submissions


@router.get("/analytics", response_model=SubmissionAnalytics)
async def get_submission_analytics(
    campaign_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics for submissions."""
    analytics = await submission_service.get_submission_analytics(
        db=db,
        recruiter_id=current_user.id,
        campaign_id=campaign_id
    )
    return analytics


# Campaign endpoints
@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new invitation campaign."""
    try:
        campaign = await submission_service.create_campaign(
            db=db,
            recruiter_id=current_user.id,
            data=data
        )
        return campaign
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create campaign"
        )


@router.get("/campaigns", response_model=List[CampaignResponse])
async def get_my_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all campaigns for the current recruiter."""
    campaigns = await submission_service.get_recruiter_campaigns(
        db=db,
        recruiter_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    # Add submission count
    for campaign in campaigns:
        from sqlalchemy import select, func
        from app.models.submission import CandidateSubmission
        
        count_query = select(func.count()).select_from(CandidateSubmission).where(
            CandidateSubmission.campaign_id == campaign.id
        )
        result = await db.execute(count_query)
        campaign.submission_count = result.scalar() or 0
    
    return campaigns


@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    data: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a campaign."""
    try:
        campaign = await submission_service.update_campaign(
            db=db,
            campaign_id=campaign_id,
            recruiter_id=current_user.id,
            data=data
        )
        return campaign
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update campaign"
        )


@router.get("/campaigns/{campaign_id}/analytics", response_model=CampaignAnalytics)
async def get_campaign_analytics(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics for a specific campaign."""
    # Verify campaign ownership
    from app.models.submission import InvitationCampaign
    campaign = await db.get(InvitationCampaign, campaign_id)
    if not campaign or campaign.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    analytics = await submission_service.get_submission_analytics(
        db=db,
        recruiter_id=current_user.id,
        campaign_id=campaign_id
    )
    
    return CampaignAnalytics(
        campaign_id=campaign_id,
        campaign_name=campaign.name,
        total_invites=analytics["total_sent"],
        total_submissions=analytics["total_submitted"],
        conversion_rate=analytics["conversion_rate"]
    )


# Public endpoints (for candidates)
@router.get("/submit/{token}", response_model=SubmissionPublicResponse)
async def get_submission_info(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Get public information about a submission (for candidates)."""
    submission = await submission_service.get_submission_by_token(
        db=db,
        token=token,
        include_campaign=True
    )
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid submission link"
        )
    
    # Get recruiter info
    recruiter = await db.get(User, submission.recruiter_id)
    
    return SubmissionPublicResponse(
        status=submission.status,
        submission_type=submission.submission_type,
        expires_at=submission.expires_at,
        recruiter_name=recruiter.full_name if recruiter else None,
        company_name=recruiter.company if recruiter else None,
        campaign_name=submission.campaign.name if submission.campaign else None,
        is_expired=submission.is_expired
    )


@router.post("/submit/{token}")
async def submit_candidate_data(
    token: str,
    data: SubmissionSubmit,
    db: AsyncSession = Depends(get_db)
):
    """Submit candidate data (public endpoint)."""
    try:
        # Log the incoming data for debugging
        logger.info(f"Received submission data for token {token}: {data.dict()}")
        
        submission = await submission_service.submit_candidate_data(
            db=db,
            token=token,
            data=data
        )
        
        # Check if this was an update or new submission
        was_update = submission.submission_type == "update"
        
        return {
            "success": True,
            "message": "Your profile has been updated successfully!" if was_update else "Your profile has been submitted successfully!",
            "submission_type": submission.submission_type,
            "was_existing": True  # This will help frontend understand what happened
        }
        
    except ValueError as e:
        logger.error(f"ValueError in submit_candidate_data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting candidate data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit data"
        )


@router.get("/campaigns/public/{slug}", response_model=CampaignPublicResponse)
async def get_public_campaign(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get public campaign information (for candidates)."""
    campaign = await submission_service.get_campaign_by_slug(db=db, slug=slug)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Check if campaign is still open
    from datetime import datetime
    is_open = True
    if campaign.auto_close_date and datetime.utcnow() > campaign.auto_close_date:
        is_open = False
    
    if campaign.max_submissions:
        from sqlalchemy import select, func
        from app.models.submission import CandidateSubmission, SubmissionStatus
        
        count_query = select(func.count()).select_from(CandidateSubmission).where(
            CandidateSubmission.campaign_id == campaign.id,
            CandidateSubmission.status.in_([SubmissionStatus.SUBMITTED, SubmissionStatus.PROCESSED])
        )
        result = await db.execute(count_query)
        submission_count = result.scalar() or 0
        
        if submission_count >= campaign.max_submissions:
            is_open = False
    
    # Get recruiter info
    recruiter = await db.get(User, campaign.recruiter_id)
    
    return CampaignPublicResponse(
        name=campaign.name,
        description=campaign.description,
        company_name=recruiter.company if recruiter else None,
        branding=campaign.branding,
        is_open=is_open
    )