"""WebSocket endpoints for real-time features."""

from fastapi import APIRouter, WebSocket, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.websocket.interview_ws import interview_websocket_endpoint
from app.api import deps
from app.db.session import async_session_maker

router = APIRouter()


@router.websocket("/ws/interview/{session_id}")
async def websocket_interview(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...)
):
    """WebSocket endpoint for real-time interview features.
    
    Connect with: ws://localhost:8000/api/v1/ws/interview/{session_id}?token={jwt_token}
    
    Message types:
    - audio_chunk: Send audio data for transcription
    - request_suggestion: Request coaching suggestions
    - sync_state: Sync interview state
    - chat_message: Send chat message
    - end_transcription: End transcription and get summary
    """
    # Get database session manually for WebSocket
    async with async_session_maker() as db:
        await interview_websocket_endpoint(websocket, session_id, token, db)