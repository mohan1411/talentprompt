"""Test endpoint for AI parsing verification."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api import deps
from app.core.config import settings
from app.models.user import User

router = APIRouter()


class AITestResponse(BaseModel):
    """AI test response."""
    openai_configured: bool
    openai_model: str
    message: str


@router.get("/test-config", response_model=AITestResponse)
async def test_ai_config(
    current_user: User = Depends(deps.get_current_active_user)
) -> AITestResponse:
    """Test if AI parsing is properly configured."""
    
    is_configured = bool(settings.OPENAI_API_KEY)
    
    return AITestResponse(
        openai_configured=is_configured,
        openai_model=settings.OPENAI_MODEL if is_configured else "Not configured",
        message="AI parsing is ready!" if is_configured else "OpenAI API key not configured"
    )