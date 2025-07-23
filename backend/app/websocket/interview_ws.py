"""WebSocket handler for real-time interview features."""

import asyncio
import json
import logging
from typing import Dict, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.config import settings
from app.services.transcription import TranscriptionService

transcription_service = TranscriptionService()
from app.services.interview_ai import interview_ai_service
from app.models.user import User
from app.models.interview import InterviewSession
from app.api.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


class ConnectionManager:
    """Manages WebSocket connections for interview sessions."""
    
    def __init__(self):
        # Maps session_id to set of connected websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Maps websocket to user info
        self.connection_users: Dict[WebSocket, Dict] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str, user_info: Dict):
        """Accept and register a new connection."""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
            
        self.active_connections[session_id].add(websocket)
        self.connection_users[websocket] = user_info
        
        # Notify others in the session
        await self.broadcast_to_session(session_id, {
            "type": "user_joined",
            "user": user_info,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude=websocket)
        
        logger.info(f"User {user_info['id']} connected to session {session_id}")
        
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a connection."""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                
        user_info = self.connection_users.pop(websocket, {})
        logger.info(f"User {user_info.get('id', 'unknown')} disconnected from session {session_id}")
        
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            
    async def broadcast_to_session(self, session_id: str, message: dict, exclude: WebSocket = None):
        """Broadcast message to all connections in a session."""
        if session_id not in self.active_connections:
            return
            
        # Ensure we have a set to iterate over
        connections = self.active_connections.get(session_id, set())
        if not isinstance(connections, set):
            logger.error(f"Invalid connections type for session {session_id}: {type(connections)}")
            return
            
        disconnected = []
        
        for connection in connections:
            if connection != exclude:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")
                    disconnected.append(connection)
                    
        # Clean up disconnected sockets
        for conn in disconnected:
            self.disconnect(conn, session_id)


# Global connection manager
manager = ConnectionManager()


async def get_current_user_from_token(token: str, db: AsyncSession) -> User:
    """Verify JWT token and return user."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
            
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
            
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def interview_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str,
    db: AsyncSession
):
    """WebSocket endpoint for real-time interview features."""
    try:
        # Authenticate user
        user = await get_current_user_from_token(token, db)
        
        # Verify user has access to this interview session
        result = await db.execute(
            select(InterviewSession).where(
                InterviewSession.id == session_id,
                InterviewSession.interviewer_id == user.id
            )
        )
        interview_session = result.scalar_one_or_none()
        
        if not interview_session:
            await websocket.close(code=4003, reason="Access denied")
            return
            
        # Connect
        user_info = {
            "id": str(user.id),
            "name": user.full_name or user.username,
            "role": "interviewer"
        }
        
        await manager.connect(websocket, session_id, user_info)
        
        # Initialize transcription session
        try:
            await transcription_service.start_session(session_id, {
                "interviewer_id": str(user.id),
                "position": interview_session.job_position,
                "interview_type": interview_session.interview_type,
                "candidate_name": "Unknown",  # TODO: Get from resume
                "job_skills": []  # TODO: Extract from job requirements
            })
        except Exception as e:
            logger.error(f"Failed to start transcription session: {e}", exc_info=True)
        
        # Send initial state
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "user": user_info,
            "features": {
                "transcription": True,
                "live_insights": True,
                "coaching": True
            }
        })
        
        # Main message loop
        while True:
            # Receive message
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "audio_chunk":
                # Handle audio data for transcription
                await handle_audio_chunk(websocket, session_id, data)
                
            elif message_type == "request_suggestion":
                # Generate coaching suggestion
                await handle_suggestion_request(websocket, session_id, data)
                
            elif message_type == "sync_state":
                # Sync interview state
                await handle_state_sync(websocket, session_id, data)
                
            elif message_type == "chat_message":
                # Handle chat between participants
                await handle_chat_message(websocket, session_id, data, user_info)
                
            elif message_type == "end_transcription":
                # End transcription and get summary
                await handle_end_transcription(websocket, session_id)
                
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        await manager.broadcast_to_session(session_id, {
            "type": "user_left",
            "user": user_info,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=4000, reason=str(e))


async def handle_audio_chunk(websocket: WebSocket, session_id: str, data: Dict):
    """Process audio chunk for transcription."""
    try:
        audio_data = data.get("audio", "")
        
        # Convert base64 to bytes if needed
        if isinstance(audio_data, str):
            import base64
            audio_data = base64.b64decode(audio_data)
            
        # Process audio
        result = await transcription_service.process_audio_chunk(
            session_id,
            audio_data,
            is_final=data.get("is_final", False)
        )
        
        if result:
            # Broadcast transcription to all participants
            await manager.broadcast_to_session(session_id, {
                "type": "transcription_update",
                "data": result
            })
            
            # Generate live insights
            if result.get("text"):
                insights = await generate_live_insights(session_id, result)
                if insights:
                    await manager.broadcast_to_session(session_id, {
                        "type": "live_insights",
                        "data": insights
                    })
                    
    except Exception as e:
        logger.error(f"Error handling audio chunk: {e}")
        await websocket.send_json({
            "type": "error",
            "message": "Failed to process audio"
        })


async def handle_suggestion_request(websocket: WebSocket, session_id: str, data: Dict):
    """Generate coaching suggestions."""
    try:
        context = data.get("context", {})
        recent_transcript = data.get("recent_transcript", "")
        
        suggestions = await transcription_service.generate_live_suggestions(
            session_id,
            recent_transcript,
            context
        )
        
        await websocket.send_json({
            "type": "coaching_suggestions",
            "data": suggestions
        })
        
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")


async def handle_state_sync(websocket: WebSocket, session_id: str, data: Dict):
    """Sync interview state across participants."""
    # Broadcast state update to others
    await manager.broadcast_to_session(session_id, {
        "type": "state_update",
        "data": data.get("state", {})
    }, exclude=websocket)


async def handle_chat_message(websocket: WebSocket, session_id: str, data: Dict, user_info: Dict):
    """Handle chat messages between participants."""
    message = {
        "type": "chat_message",
        "message": data.get("message", ""),
        "user": user_info,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Broadcast to all participants
    await manager.broadcast_to_session(session_id, message)


async def handle_end_transcription(websocket: WebSocket, session_id: str):
    """End transcription and get summary."""
    try:
        summary = await transcription_service.end_session(session_id)
        
        await websocket.send_json({
            "type": "transcription_summary",
            "data": summary
        })
        
    except Exception as e:
        logger.error(f"Error ending transcription: {e}")


async def generate_live_insights(session_id: str, transcript_data: Dict) -> Dict:
    """Generate real-time insights from transcript."""
    try:
        analysis = transcript_data.get("analysis", {})
        
        insights = {
            "sentiment": analysis.get("sentiment", {}),
            "skills_mentioned": analysis.get("skills_mentioned", []),
            "quality_indicators": analysis.get("quality_indicators", {}),
            "speaking_metrics": {
                "word_count": analysis.get("word_count", 0),
                "speaking_pace": analysis.get("speaking_pace", 0)
            }
        }
        
        # Add alerts if needed
        alerts = []
        
        # Check sentiment
        if analysis.get("sentiment", {}).get("sentiment") == "negative":
            alerts.append({
                "type": "sentiment",
                "level": "warning",
                "message": "Candidate seems to be showing negative sentiment"
            })
            
        # Check speaking pace
        pace = analysis.get("speaking_pace", 0)
        if pace > 200:
            alerts.append({
                "type": "pace",
                "level": "info",
                "message": "Candidate is speaking very quickly"
            })
        elif pace < 100 and pace > 0:
            alerts.append({
                "type": "pace",
                "level": "info",
                "message": "Candidate is speaking slowly"
            })
            
        insights["alerts"] = alerts
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return {}