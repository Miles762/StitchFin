"""
Usage metering and cost calculation
"""
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.usage import UsageEvent
from app.config import PRICING
from app.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_cost(provider: str, tokens_in: int, tokens_out: int) -> Decimal:
    """
    Calculate cost based on provider pricing

    Args:
        provider: Vendor name ('vendorA' or 'vendorB')
        tokens_in: Input tokens
        tokens_out: Output tokens

    Returns:
        Cost in USD (6 decimal places)
    """
    if provider not in PRICING:
        raise ValueError(f"Unknown provider: {provider}")

    pricing = PRICING[provider]

    input_cost = (Decimal(tokens_in) / Decimal(1000)) * pricing["input_tokens"]
    output_cost = (Decimal(tokens_out) / Decimal(1000)) * pricing["output_tokens"]

    total_cost = input_cost + output_cost

    # Round to 6 decimal places
    return total_cost.quantize(Decimal('0.000001'))


def create_usage_event(
    db: Session,
    tenant_id: UUID,
    agent_id: UUID,
    session_id: UUID,
    provider: str,
    tokens_in: int,
    tokens_out: int,
    message_id: Optional[UUID] = None,
    event_type: str = "message",
    metadata: dict = None
) -> UsageEvent:
    """
    Create and persist a usage event

    Args:
        db: Database session
        tenant_id: Tenant ID
        agent_id: Agent ID
        session_id: Session ID
        provider: Vendor name
        tokens_in: Input tokens
        tokens_out: Output tokens
        message_id: Message ID (optional)
        event_type: Event type (default 'message')
        metadata: Additional metadata (optional)

    Returns:
        Created UsageEvent
    """
    cost = calculate_cost(provider, tokens_in, tokens_out)

    usage_event = UsageEvent(
        tenant_id=tenant_id,
        agent_id=agent_id,
        session_id=session_id,
        message_id=message_id,
        provider=provider,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost,
        event_type=event_type,
        metadata=metadata or {},
        created_at=datetime.utcnow()
    )

    db.add(usage_event)
    db.commit()
    db.refresh(usage_event)

    logger.info(
        f"Usage event created",
        extra={
            "tenant_id": str(tenant_id),
            "agent_id": str(agent_id),
            "session_id": str(session_id),
            "provider": provider,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": float(cost)
        }
    )

    return usage_event
