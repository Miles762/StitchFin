"""
Text-to-Speech service using OpenAI TTS
"""
import time
from io import BytesIO
from openai import OpenAI
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TTSService:
    """Text-to-Speech service using OpenAI TTS API"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "tts-1"  # Faster, lower latency
        # self.model = "tts-1-hd"  # Higher quality
        self.voice = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer

    async def synthesize(self, text: str, voice: str = None) -> dict:
        """
        Convert text to speech using OpenAI TTS

        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)

        Returns:
            {
                "audio_data": bytes,
                "format": "mp3",
                "latency_ms": 1234
            }
        """
        start_time = time.time()

        try:
            logger.info(f"Starting TTS synthesis: {len(text)} chars, voice={voice or self.voice}")

            # Call TTS API
            response = self.client.audio.speech.create(
                model=self.model,
                voice=voice or self.voice,
                input=text,
                response_format="mp3"
            )

            # Get audio bytes
            audio_bytes = response.content

            latency_ms = int((time.time() - start_time) * 1000)

            result = {
                "audio_data": audio_bytes,
                "format": "mp3",
                "latency_ms": latency_ms,
                "size_bytes": len(audio_bytes)
            }

            logger.info(f"TTS completed in {latency_ms}ms: {len(audio_bytes)} bytes")

            return result

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"TTS failed after {latency_ms}ms: {type(e).__name__}: {str(e)}")
            raise Exception(f"Text-to-speech failed: {str(e)}")


# Singleton instance
tts_service = TTSService()
