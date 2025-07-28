"""Progressive search endpoint with real-time updates."""

import logging
import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.api import deps
from app.core.config import settings
from app.services.search import search_service
from app.models import EventType
from app.services.analytics import analytics_service

router = APIRouter()
logger = logging.getLogger(__name__)


class ProgressiveSearchQuery(BaseModel):
    """Progressive search query model."""
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(10, ge=1, le=50)
    filters: Optional[dict] = None
    context: Optional[dict] = None


@router.get("/progressive")
async def search_progressive_sse(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    token: Optional[str] = Query(None, description="JWT token for EventSource auth"),
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Progressive search endpoint that streams results using Server-Sent Events.
    
    Returns results in 3 stages:
    1. Instant results from cache/keywords
    2. Enhanced results with vector search
    3. Intelligent results with GPT-4.1-mini analysis
    """
    # Handle authentication from query param (EventSource doesn't support headers)
    current_user = None
    if token:
        try:
            from app.models.user import User
            from jose import jwt
            from app.core import security
            from app.schemas.token import TokenPayload
            
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[security.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
            user_id = UUID(str(token_data.sub))
            
            # Get user from database
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            current_user = result.scalar_one_or_none()
            
            if not current_user or not current_user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}"
            )
    else:
        # Try to get user from standard auth header
        try:
            from app.api.deps import get_current_active_user
            from fastapi import Request
            # This won't work with EventSource, but keeping for regular requests
            # current_user = await get_current_active_user(db=db)
            pass
        except:
            pass
    
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required - please provide token parameter"
        )
    
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Search service is not configured. Please set OPENAI_API_KEY."
        )
    
    async def event_generator():
        """Generate SSE events for progressive search."""
        try:
            # Track search start
            await analytics_service.track_event(
                db=db,
                event_type=EventType.SEARCH_PERFORMED,
                event_data={
                    "query": query,
                    "type": "progressive",
                    "filters": None
                },
                user_id=current_user.id
            )
            
            # Perform progressive search
            async for stage_result in search_service.search_resumes_progressive(
                db=db,
                query=query,
                user_id=current_user.id,
                limit=limit,
                filters=None
            ):
                # Format results for SSE
                event_data = {
                    "stage": stage_result["stage"],
                    "stage_number": stage_result["stage_number"],
                    "total_stages": stage_result["total_stages"],
                    "search_id": stage_result["search_id"],
                    "count": stage_result["count"],
                    "timing_ms": stage_result["timing_ms"],
                    "is_final": stage_result["is_final"],
                    "results": []
                }
                
                # Format results
                for resume_data, score in stage_result["results"]:
                    result_item = {
                        "id": resume_data["id"],
                        "first_name": resume_data["first_name"],
                        "last_name": resume_data["last_name"],
                        "current_title": resume_data.get("current_title"),
                        "location": resume_data.get("location"),
                        "years_experience": resume_data.get("years_experience"),
                        "skills": resume_data.get("skills", [])[:10],  # Limit skills
                        "score": round(score, 3),
                        "match_explanation": resume_data.get("match_explanation"),
                        "skill_analysis": resume_data.get("skill_analysis"),
                    }
                    
                    # Only include AI enhancement fields if they have content
                    if resume_data.get("key_strengths") and len(resume_data["key_strengths"]) > 0:
                        result_item["key_strengths"] = resume_data["key_strengths"]
                    if resume_data.get("potential_concerns") and len(resume_data["potential_concerns"]) > 0:
                        result_item["potential_concerns"] = resume_data["potential_concerns"]
                    if resume_data.get("interview_focus") and len(resume_data["interview_focus"]) > 0:
                        result_item["interview_focus"] = resume_data["interview_focus"]
                    if resume_data.get("hiring_recommendation"):
                        result_item["hiring_recommendation"] = resume_data["hiring_recommendation"]
                    if resume_data.get("overall_fit"):
                        result_item["overall_fit"] = resume_data["overall_fit"]
                    if resume_data.get("hidden_gems") and len(resume_data["hidden_gems"]) > 0:
                        result_item["hidden_gems"] = resume_data["hidden_gems"]
                    
                    # Add career analytics data if available
                    if resume_data.get("availability_score") is not None:
                        result_item["availability_score"] = resume_data["availability_score"]
                        print(f"[API] Adding availability_score: {resume_data['availability_score']} for {result_item['first_name']}")
                    if resume_data.get("learning_velocity") is not None:
                        result_item["learning_velocity"] = resume_data["learning_velocity"]
                    if resume_data.get("career_trajectory"):
                        result_item["career_trajectory"] = resume_data["career_trajectory"]
                    if resume_data.get("career_dna"):
                        result_item["career_dna"] = resume_data["career_dna"]
                    
                    event_data["results"].append(result_item)
                
                # Send SSE event
                yield f"data: {json.dumps(event_data)}\n\n"
                
                # Log stage completion
                logger.info(f"Progressive search stage {stage_result['stage']} completed for query '{query}'")
            
            # Send completion event
            yield f"data: {json.dumps({'event': 'complete'})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in progressive search: {e}")
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        }
    )


@router.websocket("/progressive/ws")
async def search_progressive_websocket(
    websocket: WebSocket,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    WebSocket endpoint for progressive search with real-time updates.
    
    Client sends:
    {
        "query": "search query",
        "limit": 10,
        "filters": {},
        "token": "jwt_token"
    }
    
    Server sends results in stages with the same format as SSE.
    """
    await websocket.accept()
    
    try:
        # Receive search request
        data = await websocket.receive_json()
        
        # Authenticate user
        token = data.get("token")
        if not token:
            await websocket.send_json({"error": "Authentication required"})
            await websocket.close()
            return
        
        # Verify token and get user
        try:
            from jose import jwt
            from app.core import security
            from app.schemas.token import TokenPayload
            
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[security.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
            user_id = UUID(str(token_data.sub))
            
            # Get user from database
            from app.models.user import User
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            current_user = result.scalar_one_or_none()
            
            if not current_user or not current_user.is_active:
                await websocket.send_json({"error": "Invalid user"})
                await websocket.close()
                return
                
        except Exception as e:
            await websocket.send_json({"error": "Authentication failed"})
            await websocket.close()
            return
        
        # Extract search parameters
        query = data.get("query", "")
        limit = data.get("limit", 10)
        filters = data.get("filters")
        
        # Perform progressive search
        async for stage_result in search_service.search_resumes_progressive(
            db=db,
            query=query,
            user_id=current_user.id,
            limit=limit,
            filters=filters
        ):
            # Format and send results
            event_data = {
                "stage": stage_result["stage"],
                "stage_number": stage_result["stage_number"],
                "total_stages": stage_result["total_stages"],
                "search_id": stage_result["search_id"],
                "count": stage_result["count"],
                "timing_ms": stage_result["timing_ms"],
                "is_final": stage_result["is_final"],
                "results": []
            }
            
            # Format results
            for resume_data, score in stage_result["results"]:
                result_item = {
                    "id": resume_data["id"],
                    "first_name": resume_data["first_name"],
                    "last_name": resume_data["last_name"],
                    "current_title": resume_data.get("current_title"),
                    "location": resume_data.get("location"),
                    "years_experience": resume_data.get("years_experience"),
                    "skills": resume_data.get("skills", [])[:10],
                    "score": round(score, 3),
                    "match_explanation": resume_data.get("match_explanation"),
                    "skill_analysis": resume_data.get("skill_analysis"),
                }
                
                # Only include AI enhancement fields if they have content
                if resume_data.get("key_strengths") and len(resume_data["key_strengths"]) > 0:
                    result_item["key_strengths"] = resume_data["key_strengths"]
                if resume_data.get("potential_concerns") and len(resume_data["potential_concerns"]) > 0:
                    result_item["potential_concerns"] = resume_data["potential_concerns"]
                if resume_data.get("interview_focus") and len(resume_data["interview_focus"]) > 0:
                    result_item["interview_focus"] = resume_data["interview_focus"]
                if resume_data.get("hiring_recommendation"):
                    result_item["hiring_recommendation"] = resume_data["hiring_recommendation"]
                if resume_data.get("overall_fit"):
                    result_item["overall_fit"] = resume_data["overall_fit"]
                if resume_data.get("hidden_gems") and len(resume_data["hidden_gems"]) > 0:
                    result_item["hidden_gems"] = resume_data["hidden_gems"]
                
                # Add career analytics data if available
                if resume_data.get("availability_score") is not None:
                    result_item["availability_score"] = resume_data["availability_score"]
                if resume_data.get("learning_velocity") is not None:
                    result_item["learning_velocity"] = resume_data["learning_velocity"]
                if resume_data.get("career_trajectory"):
                    result_item["career_trajectory"] = resume_data["career_trajectory"]
                if resume_data.get("career_dna"):
                    result_item["career_dna"] = resume_data["career_dna"]
                
                event_data["results"].append(result_item)
            
            await websocket.send_json(event_data)
        
        # Send completion message
        await websocket.send_json({"event": "complete"})
        
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"event": "error", "message": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.post("/analyze-query")
async def analyze_query(
    query: str = Query(..., description="Search query to analyze"),
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
):
    """
    Analyze a search query using GPT-4.1-mini for advanced understanding.
    
    Returns detailed analysis including:
    - Primary and secondary skills
    - Implied skills
    - Experience level
    - Role type
    - Search intent
    - Suggested query expansions
    """
    
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Search service is not configured. Please set OPENAI_API_KEY."
        )
    
    # Build context from user's search history (if available)
    context = {
        "user_id": str(current_user.id),
        # In a full implementation, we'd fetch user's search history and preferences
    }
    
    # Import the analyzer service
    from app.services.gpt4_query_analyzer import GPT4QueryAnalyzer
    gpt4_analyzer = GPT4QueryAnalyzer()
    
    # Analyze query
    analysis = await gpt4_analyzer.analyze_query(query, context)
    
    # Get search suggestions from the analyzer
    suggestions = gpt4_analyzer.get_search_suggestions(analysis)
    
    return {
        "query": query,
        "analysis": analysis,
        "suggestions": suggestions,
        "expansions": []  # Could be implemented to suggest related queries
    }


@router.post("/enhance-result")
async def enhance_single_result(
    resume_id: str = Query(..., description="Resume ID to enhance"),
    query: str = Query(..., description="Original search query"),
    score: float = Query(..., description="Search score", ge=0, le=1),
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
):
    """
    Generate AI insights for a single search result on demand.
    
    Used when users want AI analysis for results beyond the top 5.
    Results are cached to avoid duplicate API calls.
    """
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured. Please set OPENAI_API_KEY."
        )
    
    try:
        # Get the resume data
        from app.models.resume import Resume
        
        stmt = select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == current_user.id  # Security: ensure user owns the resume
        )
        result = await db.execute(stmt)
        resume = result.scalar_one_or_none()
        
        if not resume:
            raise HTTPException(
                status_code=404,
                detail="Resume not found"
            )
        
        # Convert to dict format
        resume_data = {
            "id": str(resume.id),
            "first_name": resume.first_name,
            "last_name": resume.last_name,
            "current_title": resume.current_title,
            "years_experience": resume.years_experience,
            "skills": resume.skills or [],
            "location": resume.location,
            "summary": resume.summary
        }
        
        # Parse the query to get context
        from app.services.query_parser import query_parser
        parsed_query = query_parser.parse_query(query)
        
        # Generate enhancement using the result enhancer
        from app.services.result_enhancer import result_enhancer
        
        enhancement = await result_enhancer._enhance_single_result(
            resume_data=resume_data,
            score=score,
            query=query,
            parsed_query=parsed_query,
            rank=6  # Use rank 6+ to indicate this is on-demand
        )
        
        return {
            "resume_id": resume_id,
            "enhancement": enhancement,
            "cached": False  # Could check if it came from cache
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enhancing result: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate AI insights"
        )