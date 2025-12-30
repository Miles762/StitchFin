"""
Agent schemas
"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import List, Optional, Dict, Any


class AgentCreate(BaseModel):
    name: str
    primary_provider: str = Field(..., pattern="^(vendorA|vendorB)$")
    fallback_provider: Optional[str] = Field(None, pattern="^(vendorA|vendorB)$")
    system_prompt: str
    enabled_tools: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    primary_provider: Optional[str] = Field(None, pattern="^(vendorA|vendorB)$")
    fallback_provider: Optional[str] = Field(None, pattern="^(vendorA|vendorB)$")
    system_prompt: Optional[str] = None
    enabled_tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    primary_provider: str
    fallback_provider: Optional[str]
    system_prompt: str
    enabled_tools: List[str]
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
