"""
Voice API endpoints - Speech-to-Text and Text-to-Speech
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Response
from sqlalchemy.orm import Session as DBSession
from typing import Optional
from uuid import UUID

from app.models.tenant import Tenant
from app.models.session import Session
from app.models.voice import VoiceArtifact
from app.utils.database import get_db
from app.middleware.auth import get_current_tenant
from app.middleware.error_handler import NotFoundException
from app.api.deps import get_correlation_id, get_idempotency_key
from app.services.voice.handler import VoiceMessageHandler
from app.config import settings

router = APIRouter()


@router.post("/{session_id}/voice/message")
async def send_voice_message(
    session_id: UUID,
    audio_file: UploadFile = File(..., description="Audio file (wav, mp3, m4a, etc.)"),
    tenant: Tenant = Depends(get_current_tenant),
    db: DBSession = Depends(get_db),
    correlation_id: Optional[str] = Depends(get_correlation_id),
    idempotency_key: Optional[str] = Depends(get_idempotency_key)
):
    """
    Send a voice message to an agent

    Flow:
    1. Upload audio file
    2. Transcribe to text (STT)
    3. Process message with AI agent
    4. Convert response to speech (TTS)
    5. Return assistant's audio response

    Returns:
    - JSON with transcription, message details, and audio download URL
    - Or direct audio file (set Accept: audio/mp3)
    """
    # Verify session belongs to tenant
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.tenant_id == tenant.id
    ).first()

    if not session:
        raise NotFoundException("Session not found")

    # Check if session is voice channel
    if session.channel != "voice":
        raise HTTPException(
            status_code=400,
            detail=f"Session channel is '{session.channel}', expected 'voice'. Create a voice session first."
        )

    # Validate file size
    max_size = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024  # Convert MB to bytes
    file_content = await audio_file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large. Maximum size: {settings.MAX_AUDIO_SIZE_MB}MB"
        )

    # Reset file pointer
    await audio_file.seek(0)

    # Process voice message
    handler = VoiceMessageHandler(db, tenant.id, session, correlation_id)

    result = await handler.handle_voice_message(
        audio_file=audio_file.file,
        filename=audio_file.filename,
        idempotency_key=idempotency_key
    )

    # Return JSON response with embedded audio (base64) or reference
    return {
        "session_id": str(session_id),
        "correlation_id": correlation_id,
        "user_message": result["user_message"],
        "assistant_message": result["assistant_message"],
        "audio_download_url": f"/api/sessions/{session_id}/voice/audio/{result['assistant_message']['id']}",
        "stt_latency_ms": result["stt_latency_ms"],
        "tts_latency_ms": result["tts_latency_ms"],
        "total_latency_ms": result["total_latency_ms"]
    }


@router.get("/{session_id}/voice/audio/{message_id}")
async def download_voice_audio(
    session_id: UUID,
    message_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: DBSession = Depends(get_db)
):
    """
    Download audio artifact for a message

    Returns the audio file (mp3) for the assistant's response
    """
    # Verify session belongs to tenant
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.tenant_id == tenant.id
    ).first()

    if not session:
        raise NotFoundException("Session not found")

    # Find audio artifact
    artifact = db.query(VoiceArtifact).filter(
        VoiceArtifact.session_id == session_id,
        VoiceArtifact.message_id == message_id,
        VoiceArtifact.artifact_type == "audio_out"
    ).first()

    if not artifact:
        raise NotFoundException("Audio artifact not found")

    # Return audio file
    return Response(
        content=artifact.audio_data,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"attachment; filename=response_{message_id}.mp3"
        }
    )


@router.get("/{session_id}/voice/artifacts")
async def list_voice_artifacts(
    session_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: DBSession = Depends(get_db)
):
    """
    List all voice artifacts for a session

    Returns both incoming (user) and outgoing (assistant) audio artifacts
    """
    # Verify session belongs to tenant
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.tenant_id == tenant.id
    ).first()

    if not session:
        raise NotFoundException("Session not found")

    # Get all artifacts
    artifacts = db.query(VoiceArtifact).filter(
        VoiceArtifact.session_id == session_id
    ).order_by(VoiceArtifact.created_at).all()

    return [
        {
            "id": str(artifact.id),
            "session_id": str(artifact.session_id),
            "message_id": str(artifact.message_id) if artifact.message_id else None,
            "artifact_type": artifact.artifact_type,
            "duration_seconds": float(artifact.duration_seconds) if artifact.duration_seconds else None,
            "transcript": artifact.transcript,
            "provider": artifact.provider,
            "latency_ms": artifact.latency_ms,
            "created_at": artifact.created_at.isoformat(),
            "download_url": f"/api/sessions/{session_id}/voice/audio/{artifact.message_id}" if artifact.message_id else None
        }
        for artifact in artifacts
    ]
