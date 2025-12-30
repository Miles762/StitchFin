"""
Speech-to-Text service using OpenAI Whisper
"""
import time
from typing import BinaryIO
from openai import OpenAI
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class STTService:
    """Speech-to-Text service using OpenAI Whisper API"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "whisper-1"

    async def transcribe(self, audio_file: BinaryIO, filename: str = "audio.wav") -> dict:
        """
        Transcribe audio to text using Whisper

        Args:
            audio_file: Binary audio file
            filename: Original filename (helps Whisper detect format)

        Returns:
            {
                "text": "transcribed text",
                "language": "en",
                "duration": 5.2,
                "latency_ms": 1234
            }
        """
        start_time = time.time()

        try:
            logger.info(f"Starting STT transcription for {filename}")

            # Call Whisper API
            transcript = self.client.audio.transcriptions.create(
                model=self.model,
                file=(filename, audio_file),
                response_format="verbose_json"
            )

            latency_ms = int((time.time() - start_time) * 1000)

            result = {
                "text": transcript.text,
                "language": transcript.language if hasattr(transcript, 'language') else "unknown",
                "duration": transcript.duration if hasattr(transcript, 'duration') else None,
                "latency_ms": latency_ms
            }

            logger.info(f"STT completed in {latency_ms}ms: {len(transcript.text)} chars")

            return result

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"STT failed after {latency_ms}ms: {type(e).__name__}: {str(e)}")
            raise Exception(f"Speech-to-text failed: {str(e)}")


# Singleton instance
stt_service = STTService()
