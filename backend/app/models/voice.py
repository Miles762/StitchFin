"""
Voice Artifact model
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, LargeBinary, Text, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.utils.database import Base


class VoiceArtifact(Base):
    __tablename__ = "voice_artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    artifact_type = Column(String(50), nullable=False)  # 'audio_in' | 'audio_out'
    audio_data = Column(LargeBinary, nullable=True)  # store small audio files
    audio_url = Column(Text, nullable=True)  # or S3 URL in production
    duration_seconds = Column(Numeric(5, 2), nullable=True)
    transcript = Column(Text, nullable=True)
    provider = Column(String(50), nullable=True)  # STT/TTS provider
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="voice_artifacts")
    message = relationship("Message", back_populates="voice_artifacts")

    def __repr__(self):
        return f"<VoiceArtifact(id={self.id}, artifact_type={self.artifact_type}, session_id={self.session_id})>"
