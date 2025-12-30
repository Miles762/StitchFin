"""
Session and Message schemas
"""
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import List, Optional, Dict, Any
from decimal import Decimal


class SessionCreate(BaseModel):
    agent_id: UUID
    customer_id: Optional[str] = None
    channel: str = "chat"
    metadata: Dict[str, Any] = {}


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    provider_used: Optional[str]
    tokens_in: Optional[int]
    tokens_out: Optional[int]
    latency_ms: Optional[int]
    tools_called: List[str]
    correlation_id: Optional[str]
    cost_usd: Optional[Decimal]
    created_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    agent_id: UUID
    customer_id: Optional[str]
    channel: str
    metadata: Dict[str, Any]
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True
