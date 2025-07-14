"""Real-time transcription service using OpenAI Whisper API."""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
import aiohttp
import io
from pydub import AudioSegment

from app.core.config import settings
from app.services.openai import openai_service

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for real-time audio transcription and analysis."""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.whisper_api_url = "https://api.openai.com/v1/audio/transcriptions"
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
    async def start_session(self, session_id: str, metadata: Dict[str, Any]) -> None:
        """Initialize a new transcription session."""
        self.active_sessions[session_id] = {
            "metadata": metadata,
            "start_time": datetime.utcnow(),
            "transcript_chunks": [],
            "audio_buffer": io.BytesIO(),
            "last_transcript_time": datetime.utcnow(),
            "speaker_segments": [],
            "interim_buffer": b"",
            "processing": False
        }
        logger.info(f"Started transcription session: {session_id}")
    
    async def process_audio_chunk(
        self, 
        session_id: str, 
        audio_data: bytes,
        is_final: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Process an audio chunk and return transcription if available."""
        if session_id not in self.active_sessions:
            logger.error(f"Session {session_id} not found")
            return None
            
        session = self.active_sessions[session_id]
        
        # Avoid concurrent processing
        if session["processing"] and not is_final:
            session["interim_buffer"] += audio_data
            return None
            
        session["processing"] = True
        
        try:
            # Add any buffered data
            if session["interim_buffer"]:
                audio_data = session["interim_buffer"] + audio_data
                session["interim_buffer"] = b""
            
            # Append to audio buffer
            session["audio_buffer"].write(audio_data)
            
            # Process when we have enough audio (e.g., 1 second) or on final chunk
            buffer_size = session["audio_buffer"].tell()
            min_chunk_size = 16000 * 2  # ~1 second of 16kHz mono audio
            
            if buffer_size >= min_chunk_size or is_final:
                # Get audio data
                session["audio_buffer"].seek(0)
                audio_to_process = session["audio_buffer"].read()
                
                # Reset buffer
                session["audio_buffer"] = io.BytesIO()
                
                # Transcribe
                transcript_data = await self._transcribe_audio(audio_to_process)
                
                if transcript_data and transcript_data.get("text"):
                    # Analyze the transcript for insights
                    analysis = await self._analyze_transcript_chunk(
                        transcript_data["text"],
                        session["metadata"]
                    )
                    
                    chunk_data = {
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "text": transcript_data["text"],
                        "duration": transcript_data.get("duration", 0),
                        "analysis": analysis,
                        "is_final": is_final
                    }
                    
                    session["transcript_chunks"].append(chunk_data)
                    
                    return chunk_data
                    
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
        finally:
            session["processing"] = False
            
        return None
    
    async def _transcribe_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """Send audio to OpenAI Whisper API for transcription."""
        try:
            # Convert audio to WAV format if needed
            audio = AudioSegment.from_raw(
                io.BytesIO(audio_data),
                sample_width=2,
                frame_rate=16000,
                channels=1
            )
            
            # Export as WAV
            wav_buffer = io.BytesIO()
            audio.export(wav_buffer, format="wav")
            wav_buffer.seek(0)
            
            # Prepare multipart data
            form_data = aiohttp.FormData()
            form_data.add_field(
                'file',
                wav_buffer,
                filename='audio.wav',
                content_type='audio/wav'
            )
            form_data.add_field('model', 'whisper-1')
            form_data.add_field('response_format', 'verbose_json')
            form_data.add_field('language', 'en')
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.whisper_api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    data=form_data
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Whisper API error: {response.status} - {error_text}")
                        return {}
                        
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {}
    
    async def _analyze_transcript_chunk(
        self, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze transcript chunk for insights."""
        try:
            # Quick sentiment analysis
            sentiment = await self._get_sentiment(text)
            
            # Extract key topics/skills mentioned
            skills_mentioned = self._extract_skills(text, metadata.get("job_skills", []))
            
            # Detect question quality indicators
            quality_indicators = self._analyze_response_quality(text)
            
            return {
                "sentiment": sentiment,
                "skills_mentioned": skills_mentioned,
                "quality_indicators": quality_indicators,
                "word_count": len(text.split()),
                "speaking_pace": self._calculate_speaking_pace(text, 1.0)  # Assume 1 second chunks
            }
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {}
    
    async def _get_sentiment(self, text: str) -> Dict[str, Any]:
        """Quick sentiment analysis using GPT-4o-mini."""
        try:
            prompt = f"""
            Analyze the sentiment of this interview response. Return JSON:
            {{
                "sentiment": "positive/neutral/negative",
                "confidence": 0.0-1.0,
                "emotion": "confident/nervous/enthusiastic/uncertain/calm"
            }}
            
            Text: {text}
            """
            
            response = await openai_service.generate_completion(
                prompt, 
                temperature=0.3,
                max_tokens=100
            )
            
            return json.loads(response)
        except:
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "emotion": "neutral"
            }
    
    def _extract_skills(self, text: str, job_skills: list) -> list:
        """Extract mentioned skills from text."""
        mentioned = []
        text_lower = text.lower()
        
        for skill in job_skills:
            if skill.lower() in text_lower:
                mentioned.append(skill)
                
        return mentioned
    
    def _analyze_response_quality(self, text: str) -> Dict[str, Any]:
        """Analyze response quality indicators."""
        words = text.split()
        
        return {
            "uses_examples": "example" in text.lower() or "instance" in text.lower(),
            "structured_response": text.count('.') > 2,  # Multiple sentences
            "uses_numbers": any(char.isdigit() for char in text),
            "confidence_words": sum(1 for word in ["definitely", "certainly", "absolutely", "clearly"] if word in text.lower()),
            "hedge_words": sum(1 for word in ["maybe", "perhaps", "might", "possibly", "probably"] if word in text.lower())
        }
    
    def _calculate_speaking_pace(self, text: str, duration: float) -> float:
        """Calculate words per minute."""
        word_count = len(text.split())
        if duration > 0:
            return (word_count / duration) * 60
        return 0
    
    async def generate_live_suggestions(
        self, 
        session_id: str,
        recent_transcript: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate real-time coaching suggestions."""
        try:
            prompt = f"""
            You are an interview coach providing real-time suggestions.
            
            Context:
            - Position: {context.get('position', 'Unknown')}
            - Current Question: {context.get('current_question', 'Unknown')}
            - Interview Type: {context.get('interview_type', 'general')}
            
            Recent Response: {recent_transcript}
            
            Provide coaching suggestions in JSON:
            {{
                "follow_up_questions": ["question1", "question2"],
                "dig_deeper_prompts": ["prompt if answer is surface level"],
                "coaching_tips": ["tip for interviewer"],
                "red_flags": ["any concerns"],
                "positive_signals": ["good signs noticed"]
            }}
            
            Be concise and actionable.
            """
            
            response = await openai_service.generate_completion(
                prompt,
                temperature=0.7,
                max_tokens=300
            )
            
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return {
                "follow_up_questions": [],
                "dig_deeper_prompts": [],
                "coaching_tips": [],
                "red_flags": [],
                "positive_signals": []
            }
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """End transcription session and return summary."""
        if session_id not in self.active_sessions:
            return {}
            
        session = self.active_sessions[session_id]
        
        # Process any remaining audio
        if session["audio_buffer"].tell() > 0:
            await self.process_audio_chunk(session_id, b"", is_final=True)
        
        # Generate session summary
        full_transcript = " ".join([
            chunk["text"] for chunk in session["transcript_chunks"]
        ])
        
        summary = await self._generate_session_summary(
            full_transcript,
            session["transcript_chunks"],
            session["metadata"]
        )
        
        # Clean up
        del self.active_sessions[session_id]
        
        return summary
    
    async def _generate_session_summary(
        self,
        full_transcript: str,
        chunks: list,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive session summary."""
        try:
            # Aggregate sentiment
            sentiments = [c["analysis"].get("sentiment", {}) for c in chunks if c.get("analysis")]
            
            # Calculate speaking time
            total_duration = sum(c.get("duration", 0) for c in chunks)
            
            # Generate AI summary
            prompt = f"""
            Summarize this interview session:
            
            Position: {metadata.get('position')}
            Candidate: {metadata.get('candidate_name')}
            
            Transcript: {full_transcript[:3000]}...
            
            Provide a JSON summary:
            {{
                "key_points": ["main discussion points"],
                "skills_demonstrated": ["skills shown"],
                "strengths": ["candidate strengths"],
                "areas_for_improvement": ["areas to explore further"],
                "overall_impression": "brief overall assessment",
                "recommended_next_steps": ["next steps"]
            }}
            """
            
            ai_summary = await openai_service.generate_completion(prompt, temperature=0.5)
            
            return {
                "session_duration": total_duration,
                "total_words": len(full_transcript.split()),
                "sentiment_summary": self._aggregate_sentiments(sentiments),
                "ai_summary": json.loads(ai_summary),
                "transcript": full_transcript,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                "error": "Failed to generate summary",
                "transcript": full_transcript
            }
    
    def _aggregate_sentiments(self, sentiments: list) -> Dict[str, Any]:
        """Aggregate sentiment data."""
        if not sentiments:
            return {}
            
        positive = sum(1 for s in sentiments if s.get("sentiment") == "positive")
        negative = sum(1 for s in sentiments if s.get("sentiment") == "negative")
        neutral = sum(1 for s in sentiments if s.get("sentiment") == "neutral")
        
        total = len(sentiments)
        
        return {
            "positive_ratio": positive / total if total > 0 else 0,
            "negative_ratio": negative / total if total > 0 else 0,
            "neutral_ratio": neutral / total if total > 0 else 0,
            "dominant_sentiment": max(
                [("positive", positive), ("negative", negative), ("neutral", neutral)],
                key=lambda x: x[1]
            )[0]
        }


# Singleton instance
transcription_service = TranscriptionService()