"""
Analytics schemas
"""
from pydantic import BaseModel
from decimal import Decimal
from typing import Dict, List
from uuid import UUID


class ProviderStats(BaseModel):
    sessions: int
    tokens_in: int
    tokens_out: int
    cost_usd: Decimal


class UsageAnalytics(BaseModel):
    total_sessions: int
    total_messages: int
    total_tokens_in: int
    total_tokens_out: int
    total_cost_usd: Decimal
    breakdown_by_provider: Dict[str, ProviderStats]


class TopAgent(BaseModel):
    agent_id: UUID
    agent_name: str
    total_sessions: int
    total_cost_usd: Decimal
    total_tokens: int


class TopAgentsResponse(BaseModel):
    agents: List[TopAgent]
