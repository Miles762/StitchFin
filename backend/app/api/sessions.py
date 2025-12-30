"""
Session and Message API endpoints
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session as DBSession
from typing import Optional
from uuid import UUID

from app.models.tenant import Tenant
from app.models.agent import Agent
from app.models.session import Session, Message
from app.schemas.session import SessionCreate, SessionResponse, MessageCreate, MessageResponse
from app.utils.database import get_db
from app.middleware.auth import get_current_tenant
from app.middleware.error_handler import NotFoundException
from app.api.deps import get_correlation_id, get_idempotency_key
from app.services.message_handler import MessageHandler

router = APIRouter()


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    session_data: SessionCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: DBSession = Depends(get_db)
):
    """Create a new conversation session"""
    # Verify agent belongs to tenant
    agent = db.query(Agent).filter(
        Agent.id == session_data.agent_id,
        Agent.tenant_id == tenant.id
    ).first()

    if not agent:
        raise NotFoundException("Agent not found")

    session = Session(
        tenant_id=tenant.id,
        agent_id=session_data.agent_id,
        customer_id=session_data.customer_id,
        channel=session_data.channel,
        metadata=session_data.metadata
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: DBSession = Depends(get_db)
):
    """Get session with full transcript"""
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.tenant_id == tenant.id
    ).first()

    if not session:
        raise NotFoundException("Session not found")

    # Load messages
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at).all()

    # Convert messages to MessageResponse with cost calculation
    from app.services.billing.metering import calculate_cost
    message_responses = []
    for msg in messages:
        # Calculate cost if tokens are available
        cost_usd = "0.000000"
        if msg.tokens_in and msg.tokens_out and msg.provider_used:
            cost_usd = str(calculate_cost(
                provider=msg.provider_used,
                tokens_in=msg.tokens_in,
                tokens_out=msg.tokens_out
            ))

        message_responses.append(MessageResponse(
            id=msg.id,
            session_id=msg.session_id,
            role=msg.role,
            content=msg.content,
            provider_used=msg.provider_used,
            tokens_in=msg.tokens_in,
            tokens_out=msg.tokens_out,
            latency_ms=msg.latency_ms,
            tools_called=msg.tools_called,
            correlation_id=msg.correlation_id,
            cost_usd=cost_usd,
            created_at=msg.created_at
        ))

    return SessionResponse(
        id=session.id,
        tenant_id=session.tenant_id,
        agent_id=session.agent_id,
        customer_id=session.customer_id,
        channel=session.channel,
        metadata=session.session_metadata or {},
        created_at=session.created_at,
        messages=message_responses
    )


@router.post("/{session_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    session_id: UUID,
    message_data: MessageCreate,
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
    db: DBSession = Depends(get_db),
    correlation_id: Optional[str] = Depends(get_correlation_id),
    idempotency_key: Optional[str] = Depends(get_idempotency_key)
):
    """Send a message in a session"""
    from app.utils.logger import get_logger
    logger = get_logger(__name__)

    try:
        # Verify session belongs to tenant
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.tenant_id == tenant.id
        ).first()

        if not session:
            raise NotFoundException("Session not found")

        # Use MessageHandler to process the message
        handler = MessageHandler(db, tenant.id, session, correlation_id)
        response = await handler.handle_message(message_data.content, idempotency_key)

        return response
    except Exception as e:
        logger.error(f"Error in send_message: {type(e).__name__}: {str(e)}", exc_info=True)
        raise
