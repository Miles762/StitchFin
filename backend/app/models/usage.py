"""
Usage and Provider Call models
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.utils.database import Base


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    provider = Column(String(50), nullable=False)
    tokens_in = Column(Integer, nullable=False)
    tokens_out = Column(Integer, nullable=False)
    cost_usd = Column(Numeric(10, 6), nullable=False)
    event_type = Column(String(50), default="message", nullable=False)  # 'message' | 'voice_stt' | 'voice_tts'
    usage_metadata = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="usage_events")
    agent = relationship("Agent", back_populates="usage_events")
    session = relationship("Session", back_populates="usage_events")
    message = relationship("Message", back_populates="usage_events")

    def __repr__(self):
        return f"<UsageEvent(id={self.id}, provider={self.provider}, cost_usd={self.cost_usd})>"


class ProviderCall(Base):
    __tablename__ = "provider_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    correlation_id = Column(String(255), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)  # 'success' | 'retry' | 'fallback' | 'error'
    http_status = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="provider_calls")

    def __repr__(self):
        return f"<ProviderCall(id={self.id}, provider={self.provider}, status={self.status})>"
