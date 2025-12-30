"""
Agent model
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.utils.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    primary_provider = Column(String(50), nullable=False)  # 'vendorA' | 'vendorB'
    fallback_provider = Column(String(50), nullable=True)  # optional
    system_prompt = Column(Text, nullable=False)
    enabled_tools = Column(JSON, default=list, nullable=False)  # ['invoice_lookup', ...]
    config = Column(JSON, default=dict, nullable=False)  # extra config
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="agents")
    sessions = relationship("Session", back_populates="agent", cascade="all, delete-orphan")
    usage_events = relationship("UsageEvent", back_populates="agent")
    tool_executions = relationship("ToolExecution", back_populates="agent")

    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name}, primary_provider={self.primary_provider})>"
