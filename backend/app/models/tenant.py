"""
Tenant model
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.utils.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    company_key = Column(String(100), nullable=True)  # For company-specific data isolation
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    agents = relationship("Agent", back_populates="tenant", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="tenant", cascade="all, delete-orphan")
    usage_events = relationship("UsageEvent", back_populates="tenant")
    provider_calls = relationship("ProviderCall", back_populates="tenant")
    tool_executions = relationship("ToolExecution", back_populates="tenant")
    idempotency_keys = relationship("IdempotencyKey", back_populates="tenant")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name})>"
