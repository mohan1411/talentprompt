"""Debug endpoint to check for duplicate profiles."""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api import deps
from app.models.user import User
from app.models.resume import Resume

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/check", response_model=Dict[str, Any])
async def check_duplicates(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """Check for duplicate profiles."""
    
    # Find all Sunil profiles
    sunil_stmt = select(Resume).where(
        Resume.first_name == "Sunil",
        Resume.last_name == "Narasimhappa"
    )
    sunil_result = await db.execute(sunil_stmt)
    sunil_profiles = sunil_result.scalars().all()
    
    # Find all Anil profiles
    anil_stmt = select(Resume).where(
        Resume.first_name == "Anil",
        Resume.last_name == "Narasimhappa"
    )
    anil_result = await db.execute(anil_stmt)
    anil_profiles = anil_result.scalars().all()
    
    # Check for name duplicates
    dup_stmt = select(
        Resume.first_name,
        Resume.last_name,
        func.count(Resume.id).label('count')
    ).group_by(
        Resume.first_name,
        Resume.last_name
    ).having(
        func.count(Resume.id) > 1
    )
    
    dup_result = await db.execute(dup_stmt)
    duplicates = dup_result.all()
    
    return {
        "sunil_profiles": [
            {
                "id": str(p.id),
                "name": f"{p.first_name} {p.last_name}",
                "skills": p.skills,
                "current_title": p.current_title,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in sunil_profiles
        ],
        "anil_profiles": [
            {
                "id": str(p.id),
                "name": f"{p.first_name} {p.last_name}",
                "skills": p.skills,
                "current_title": p.current_title,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in anil_profiles
        ],
        "duplicates": [
            {
                "name": f"{d.first_name} {d.last_name}",
                "count": d.count
            }
            for d in duplicates
        ]
    }