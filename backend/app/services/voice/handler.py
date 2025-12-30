"""
Voice message handler - orchestrates STT, message processing, and TTS
"""
from typing import BinaryIO
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.session import Session as SessionModel, Message
from app.models.voice import VoiceArtifact
from app.services.voice.stt import stt_service
from app.services.voice.tts import tts_service
from app.services.message_handler import MessageHandler
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VoiceMessageHandler:
    """Handles voice message flow: STT -> Message Processing -> TTS"""

    def __init__(self, db: Session, tenant_id: UUID, session: SessionModel, correlation_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.session = session
        self.correlation_id = correlation_id
        self.logger = get_logger(__name__)

    async def handle_voice_message(
        self,
        audio_file: BinaryIO,
        filename: str = "audio.wav",
        idempotency_key: str = None
    ) -> dict:
        """
        Process voice message end-to-end

        Flow:
        1. STT: Audio -> Text
        2. Save incoming audio artifact
        3. Process text message (AI response)
        4. TTS: AI response -> Audio
        5. Save outgoing audio artifact
        6. Return response with audio

        Args:
            audio_file: Incoming audio file
            filename: Original filename
            idempotency_key: For idempotent processing

        Returns:
            {
                "user_message": {...},
                "assistant_message": {...},
                "assistant_audio": bytes,
                "stt_latency_ms": 1234,
                "tts_latency_ms": 2345
            }
        """
        try:
            # Step 1: Transcribe audio to text (STT)
            self.logger.info(f"[Voice] Step 1: Starting STT for session {self.session.id}")
            stt_result = await stt_service.transcribe(audio_file, filename)
            transcribed_text = stt_result["text"]
            stt_latency = stt_result["latency_ms"]

            self.logger.info(f"[Voice] STT completed: '{transcribed_text}' ({stt_latency}ms)")

            # Step 2: Save incoming audio artifact
            # Read audio file again for storage
            audio_file.seek(0)
            audio_data = audio_file.read()

            # Step 3: Process text message through normal message handler
            self.logger.info(f"[Voice] Step 3: Processing text message")
            message_handler = MessageHandler(
                db=self.db,
                tenant_id=self.tenant_id,
                session=self.session,
                correlation_id=self.correlation_id
            )

            assistant_message = await message_handler.handle_message(
                user_message=transcribed_text,
                idempotency_key=idempotency_key
            )

            # Get the assistant's text response
            assistant_text = assistant_message.content

            # Step 4: Convert assistant response to speech (TTS)
            self.logger.info(f"[Voice] Step 4: Starting TTS for response")
            tts_result = await tts_service.synthesize(assistant_text)
            assistant_audio = tts_result["audio_data"]
            tts_latency = tts_result["latency_ms"]

            self.logger.info(f"[Voice] TTS completed: {len(assistant_audio)} bytes ({tts_latency}ms)")

            # Step 5: Save voice artifacts to database
            # Incoming audio (user's voice)
            incoming_artifact = VoiceArtifact(
                session_id=self.session.id,
                message_id=None,  # User message (we could link if we create user message separately)
                artifact_type="audio_in",
                audio_data=audio_data,
                duration_seconds=stt_result.get("duration"),
                transcript=transcribed_text,
                provider="openai-whisper",
                latency_ms=stt_latency
            )
            self.db.add(incoming_artifact)

            # Outgoing audio (assistant's voice)
            outgoing_artifact = VoiceArtifact(
                session_id=self.session.id,
                message_id=assistant_message.id,
                artifact_type="audio_out",
                audio_data=assistant_audio,
                duration_seconds=None,  # We could calculate from audio length
                transcript=assistant_text,
                provider="openai-tts",
                latency_ms=tts_latency
            )
            self.db.add(outgoing_artifact)

            self.db.commit()

            self.logger.info(f"[Voice] Voice artifacts saved to database")

            # Step 6: Return complete response
            return {
                "user_message": {
                    "content": transcribed_text,
                    "language": stt_result.get("language"),
                    "duration_seconds": stt_result.get("duration")
                },
                "assistant_message": {
                    "id": str(assistant_message.id),
                    "content": assistant_text,
                    "provider_used": assistant_message.provider_used,
                    "tokens_in": assistant_message.tokens_in,
                    "tokens_out": assistant_message.tokens_out,
                    "latency_ms": assistant_message.latency_ms,
                    "correlation_id": assistant_message.correlation_id
                },
                "assistant_audio": assistant_audio,
                "assistant_audio_format": "mp3",
                "stt_latency_ms": stt_latency,
                "tts_latency_ms": tts_latency,
                "total_latency_ms": stt_latency + assistant_message.latency_ms + tts_latency
            }

        except Exception as e:
            self.logger.error(f"[Voice] Voice message processing failed: {type(e).__name__}: {str(e)}", exc_info=True)
            raise
