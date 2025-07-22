"""Transcription service for interview recordings."""

import os
import logging
from typing import Dict, Any, List, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio/video files with speaker diarization."""
    
    def __init__(self):
        self.assemblyai_key = settings.ASSEMBLYAI_API_KEY if hasattr(settings, 'ASSEMBLYAI_API_KEY') else None
        self.api_base = "https://api.assemblyai.com/v2"
        
    async def transcribe_with_speakers(self, file_path: str) -> Dict[str, Any]:
        """
        Transcribe an audio/video file with speaker diarization.
        
        Returns:
            Dict containing transcript with speaker labels and metadata
        """
        if not self.assemblyai_key:
            logger.warning("AssemblyAI API key not configured, using mock transcription")
            return self._mock_transcription()
            
        try:
            # Upload file to AssemblyAI
            upload_url = await self._upload_file(file_path)
            
            # Request transcription with speaker diarization
            transcript_id = await self._request_transcription(upload_url)
            
            # Poll for completion
            transcript = await self._poll_transcript(transcript_id)
            
            # Process and return results
            return self._process_transcript(transcript)
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
            
    async def _upload_file(self, file_path: str) -> str:
        """Upload file to AssemblyAI and return upload URL."""
        headers = {"authorization": self.assemblyai_key}
        
        async with httpx.AsyncClient() as client:
            with open(file_path, 'rb') as f:
                response = await client.post(
                    f"{self.api_base}/upload",
                    headers=headers,
                    files={"file": f}
                )
                response.raise_for_status()
                return response.json()["upload_url"]
                
    async def _request_transcription(self, audio_url: str) -> str:
        """Request transcription with speaker diarization."""
        headers = {
            "authorization": self.assemblyai_key,
            "content-type": "application/json"
        }
        
        data = {
            "audio_url": audio_url,
            "speaker_labels": True,  # Enable speaker diarization
            "speakers_expected": 2,  # Typically interviewer + candidate
            "punctuate": True,
            "format_text": True,
            "sentiment_analysis": True  # Get sentiment for each utterance
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/transcript",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()["id"]
            
    async def _poll_transcript(self, transcript_id: str) -> Dict[str, Any]:
        """Poll for transcript completion."""
        headers = {"authorization": self.assemblyai_key}
        
        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(
                    f"{self.api_base}/transcript/{transcript_id}",
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                status = result["status"]
                
                if status == "completed":
                    return result
                elif status == "error":
                    raise Exception(f"Transcription failed: {result.get('error')}")
                    
                # Wait before polling again
                await asyncio.sleep(5)
                
    def _process_transcript(self, transcript: Dict[str, Any]) -> Dict[str, Any]:
        """Process transcript and extract speaker segments."""
        utterances = transcript.get("utterances", [])
        
        # Group utterances by speaker
        speakers = {}
        for utterance in utterances:
            speaker = utterance["speaker"]
            if speaker not in speakers:
                speakers[speaker] = {
                    "utterances": [],
                    "total_words": 0,
                    "total_time": 0,
                    "sentiment_scores": []
                }
                
            speakers[speaker]["utterances"].append({
                "text": utterance["text"],
                "start": utterance["start"],
                "end": utterance["end"],
                "confidence": utterance["confidence"],
                "sentiment": utterance.get("sentiment"),
                "sentiment_confidence": utterance.get("sentiment_confidence")
            })
            
            speakers[speaker]["total_words"] += len(utterance["words"])
            speakers[speaker]["total_time"] += (utterance["end"] - utterance["start"])
            
            if utterance.get("sentiment"):
                speakers[speaker]["sentiment_scores"].append(
                    utterance["sentiment_confidence"]
                )
                
        # Identify likely interviewer vs candidate
        speaker_analysis = self._identify_roles(speakers)
        
        return {
            "transcript_text": transcript["text"],
            "speakers": speaker_analysis,
            "duration": transcript["audio_duration"],
            "confidence": transcript["confidence"],
            "utterances": utterances
        }
        
    def _identify_roles(self, speakers: Dict[str, Any]) -> Dict[str, Any]:
        """Identify which speaker is likely the interviewer vs candidate."""
        # Simple heuristic: interviewer asks more questions (shorter utterances)
        # and speaks less overall
        
        speaker_stats = []
        for speaker_id, data in speakers.items():
            avg_utterance_length = (
                data["total_time"] / len(data["utterances"])
                if data["utterances"] else 0
            )
            
            # Count question indicators
            question_count = sum(
                1 for u in data["utterances"]
                if any(q in u["text"].lower() for q in [
                    "tell me", "can you", "how did", "what is",
                    "why did", "describe", "explain"
                ])
            )
            
            speaker_stats.append({
                "speaker_id": speaker_id,
                "avg_utterance_length": avg_utterance_length,
                "question_ratio": question_count / len(data["utterances"]) if data["utterances"] else 0,
                "speaking_time_ratio": data["total_time"]
            })
            
        # Sort by question ratio (higher = more likely interviewer)
        speaker_stats.sort(key=lambda x: x["question_ratio"], reverse=True)
        
        # Assign roles
        result = {}
        for i, stat in enumerate(speaker_stats):
            role = "interviewer" if i == 0 else f"candidate_{i}" if i == 1 else f"participant_{i}"
            result[stat["speaker_id"]] = {
                **speakers[stat["speaker_id"]],
                "likely_role": role,
                "confidence": stat["question_ratio"]  # How confident we are in role assignment
            }
            
        return result
        
    def _mock_transcription(self) -> Dict[str, Any]:
        """Return mock transcription for testing."""
        return {
            "transcript_text": "This is a mock transcription for testing purposes.",
            "speakers": {
                "A": {
                    "utterances": [
                        {
                            "text": "Tell me about your experience with Python.",
                            "start": 0,
                            "end": 3000,
                            "confidence": 0.95,
                            "sentiment": "neutral"
                        }
                    ],
                    "likely_role": "interviewer",
                    "confidence": 0.9
                },
                "B": {
                    "utterances": [
                        {
                            "text": "I have 5 years of experience with Python...",
                            "start": 3500,
                            "end": 15000,
                            "confidence": 0.92,
                            "sentiment": "positive"
                        }
                    ],
                    "likely_role": "candidate_1",
                    "confidence": 0.85
                }
            },
            "duration": 20,
            "confidence": 0.93
        }


# Singleton instance
transcription_service = TranscriptionService()


# Import asyncio for sleep
import asyncio