"""
Integration test for message → usage billing flow

This test validates the core requirement:
"1 integration test for 'message -> usage billed'"

Tests the complete flow from sending a message through to usage event creation,
including idempotency to prevent double-billing.
"""
import pytest
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from app.models.session import Session as SessionModel, Message
from app.models.agent import Agent
from app.models.tenant import Tenant
from app.models.usage import UsageEvent
from app.services.message_handler import MessageHandler
from app.services.billing.metering import calculate_cost, create_usage_event
from app.services.vendors.base import NormalizedResponse


@pytest.mark.integration
@pytest.mark.asyncio
async def test_message_creates_usage_event(
    db_session: Session,
    test_tenant: Tenant,
    test_agent: Agent,
    test_session: SessionModel
):
    """
    Integration test: Sending a message creates a billed usage event

    Flow:
    1. Create session (via fixture)
    2. Send message through MessageHandler
    3. Verify message created in database
    4. Verify usage event created with correct cost
    """

    # Mock vendor response to avoid actual vendor calls
    mock_vendor_response = NormalizedResponse(
        text="Hello! I'm a test assistant response.",
        tokens_in=50,
        tokens_out=120,
        latency_ms=250
    )

    # Patch the resilient caller to return our mock response
    with patch('app.services.message_handler.ResilientVendorCaller') as mock_caller_class:
        mock_caller = AsyncMock()
        mock_caller.call_with_fallback = AsyncMock(return_value=mock_vendor_response)
        mock_caller_class.return_value = mock_caller

        # Create message handler
        handler = MessageHandler(
            db=db_session,
            tenant_id=test_tenant.id,
            session=test_session,
            correlation_id="test-correlation-001"
        )

        # Send message
        user_content = "Hello, test message!"
        response = await handler.handle_message(
            user_message=user_content,
            idempotency_key="test-idempotency-key-001"
        )

        # Verify response was returned
        assert response is not None
        assert response.content == mock_vendor_response.text

        # Verify user message was created in database
        user_messages = db_session.query(Message).filter(
            Message.session_id == test_session.id,
            Message.role == "user"
        ).all()
        assert len(user_messages) == 1
        assert user_messages[0].content == user_content

        # Verify assistant message was created in database
        assistant_messages = db_session.query(Message).filter(
            Message.session_id == test_session.id,
            Message.role == "assistant"
        ).all()
        assert len(assistant_messages) == 1
        assert assistant_messages[0].content == mock_vendor_response.text
        assert assistant_messages[0].tokens_in == 50
        assert assistant_messages[0].tokens_out == 120
        assert assistant_messages[0].provider_used == "vendorA"

        # Verify usage event was created with correct billing
        usage_events = db_session.query(UsageEvent).filter(
            UsageEvent.session_id == test_session.id
        ).all()
        assert len(usage_events) == 1

        usage_event = usage_events[0]
        assert usage_event.tenant_id == test_tenant.id
        assert usage_event.agent_id == test_agent.id
        assert usage_event.session_id == test_session.id
        assert usage_event.provider == "vendorA"
        assert usage_event.tokens_in == 50
        assert usage_event.tokens_out == 120

        # Verify cost calculation is correct
        # VendorA: $0.002 per 1K tokens
        # (50 + 120) / 1000 * 0.002 = 0.000340
        expected_cost = calculate_cost("vendorA", tokens_in=50, tokens_out=120)
        assert usage_event.cost_usd == expected_cost
        assert usage_event.cost_usd == Decimal("0.000340")

        # Verify event type
        assert usage_event.event_type == "message"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_idempotency_prevents_double_billing(
    db_session: Session,
    test_tenant: Tenant,
    test_agent: Agent,
    test_session: SessionModel
):
    """
    Integration test: Idempotency prevents double-billing

    Flow:
    1. Send message with idempotency key
    2. Verify usage event created
    3. Send SAME message with SAME idempotency key
    4. Verify NO new usage event created (still only 1)
    5. Verify cached response returned
    """

    # Mock vendor response
    mock_vendor_response = NormalizedResponse(
        text="Idempotent test response.",
        tokens_in=30,
        tokens_out=80,
        latency_ms=200
    )

    idempotency_key = "test-idempotent-key-unique-001"

    with patch('app.services.message_handler.ResilientVendorCaller') as mock_caller_class:
        mock_caller = AsyncMock()
        mock_caller.call_with_fallback = AsyncMock(return_value=mock_vendor_response)
        mock_caller_class.return_value = mock_caller

        handler = MessageHandler(
            db=db_session,
            tenant_id=test_tenant.id,
            session=test_session,
            correlation_id="test-correlation-002"
        )

        # First request - should create new message and billing event
        response1 = await handler.handle_message(
            user_message="Idempotent test message",
            idempotency_key=idempotency_key
        )

        assert response1 is not None
        assert response1.content == mock_vendor_response.text

        # Verify first usage event created
        usage_events_after_first = db_session.query(UsageEvent).filter(
            UsageEvent.session_id == test_session.id
        ).all()
        assert len(usage_events_after_first) == 1
        first_event = usage_events_after_first[0]
        # Provider comes from agent's primary_provider
        assert first_event.provider == test_agent.primary_provider
        assert first_event.tokens_in == 30
        assert first_event.tokens_out == 80
        expected_cost = calculate_cost(test_agent.primary_provider, tokens_in=30, tokens_out=80)
        assert first_event.cost_usd == expected_cost

        # Count messages before second request
        messages_after_first = db_session.query(Message).filter(
            Message.session_id == test_session.id
        ).count()

        # Second request with SAME idempotency key - should return cached response
        response2 = await handler.handle_message(
            user_message="Idempotent test message",  # Same message
            idempotency_key=idempotency_key  # Same key!
        )

        # Response should be identical (from cache)
        assert response2 is not None
        assert response2.content == response1.content
        assert response2.tokens_in == response1.tokens_in
        assert response2.tokens_out == response1.tokens_out

        # Verify NO new usage event created (still only 1)
        usage_events_after_second = db_session.query(UsageEvent).filter(
            UsageEvent.session_id == test_session.id
        ).all()
        assert len(usage_events_after_second) == 1  # Still only 1!

        # Verify NO new messages created (idempotent request should skip processing)
        messages_after_second = db_session.query(Message).filter(
            Message.session_id == test_session.id
        ).count()
        assert messages_after_second == messages_after_first  # Same count

        # Verify the vendor was NOT called second time (cached response used)
        # The mock should have been called only once
        assert mock_caller.call_with_fallback.call_count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_different_providers_different_costs(
    db_session: Session,
    test_tenant: Tenant
):
    """
    Integration test: Different providers result in different costs

    Validates that the billing system correctly applies different pricing
    for VendorA vs VendorB.
    """

    # Create agent with VendorA as primary
    agent_a = Agent(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="VendorA Test Agent",
        primary_provider="vendorA",
        fallback_provider=None,
        system_prompt="Test assistant",
        enabled_tools=[]
    )
    db_session.add(agent_a)
    db_session.commit()
    db_session.refresh(agent_a)

    session_a = SessionModel(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        agent_id=agent_a.id,
        customer_id="test-customer-vendor-a",
        channel="chat",
        metadata={}
    )
    db_session.add(session_a)
    db_session.commit()
    db_session.refresh(session_a)

    # Test VendorA pricing ($0.002 per 1K tokens)
    mock_vendor_a_response = NormalizedResponse(
        text="Response from VendorA",
        tokens_in=1000,
        tokens_out=1000,
        latency_ms=300
    )

    with patch('app.services.message_handler.ResilientVendorCaller') as mock_caller_class:
        mock_caller = AsyncMock()
        mock_caller.call_with_fallback = AsyncMock(return_value=mock_vendor_a_response)
        mock_caller_class.return_value = mock_caller

        handler = MessageHandler(
            db=db_session,
            tenant_id=test_tenant.id,
            session=session_a,
            correlation_id="test-correlation-003"
        )

        await handler.handle_message(
            user_message="Test VendorA pricing",
            idempotency_key="test-vendor-a-key"
        )

        # Verify VendorA cost
        # (1000 + 1000) / 1000 * 0.002 = 0.004
        vendor_a_events = db_session.query(UsageEvent).filter(
            UsageEvent.provider == "vendorA"
        ).all()
        assert len(vendor_a_events) == 1
        assert vendor_a_events[0].cost_usd == Decimal("0.004000")

    # Create agent with VendorB as primary
    agent_b = Agent(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="VendorB Test Agent",
        primary_provider="vendorB",
        fallback_provider=None,
        system_prompt="Test assistant",
        enabled_tools=[]
    )
    db_session.add(agent_b)
    db_session.commit()
    db_session.refresh(agent_b)

    session_b = SessionModel(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        agent_id=agent_b.id,
        customer_id="test-customer-vendor-b",
        channel="chat",
        metadata={}
    )
    db_session.add(session_b)
    db_session.commit()
    db_session.refresh(session_b)

    # Test VendorB pricing ($0.003 per 1K tokens)
    mock_vendor_b_response = NormalizedResponse(
        text="Response from VendorB",
        tokens_in=1000,
        tokens_out=1000,
        latency_ms=350
    )

    with patch('app.services.message_handler.ResilientVendorCaller') as mock_caller_class:
        mock_caller = AsyncMock()
        mock_caller.call_with_fallback = AsyncMock(return_value=mock_vendor_b_response)
        mock_caller_class.return_value = mock_caller

        handler_b = MessageHandler(
            db=db_session,
            tenant_id=test_tenant.id,
            session=session_b,
            correlation_id="test-correlation-004"
        )

        await handler_b.handle_message(
            user_message="Test VendorB pricing",
            idempotency_key="test-vendor-b-key"
        )

        # Verify VendorB cost
        # (1000 + 1000) / 1000 * 0.003 = 0.006
        vendor_b_events = db_session.query(UsageEvent).filter(
            UsageEvent.provider == "vendorB"
        ).all()
        assert len(vendor_b_events) == 1
        assert vendor_b_events[0].cost_usd == Decimal("0.006000")

    # Verify VendorB is 1.5x more expensive than VendorA for same token count
    vendor_a_cost = vendor_a_events[0].cost_usd
    vendor_b_cost = vendor_b_events[0].cost_usd
    assert vendor_b_cost == vendor_a_cost * Decimal("1.5")


@pytest.mark.integration
def test_usage_event_direct_creation(
    db_session: Session,
    test_tenant: Tenant,
    test_agent: Agent,
    test_session: SessionModel
):
    """
    Integration test: Direct usage event creation function

    Tests the create_usage_event function directly to ensure
    it correctly calculates and persists billing events.
    """

    # Create usage event directly
    usage_event = create_usage_event(
        db=db_session,
        tenant_id=test_tenant.id,
        agent_id=test_agent.id,
        session_id=test_session.id,
        provider="vendorA",
        tokens_in=500,
        tokens_out=300,
        event_type="test_direct",
        metadata={"test": "direct_creation"}
    )

    # Verify event was created and persisted
    assert usage_event.id is not None
    assert usage_event.tenant_id == test_tenant.id
    assert usage_event.agent_id == test_agent.id
    assert usage_event.session_id == test_session.id
    assert usage_event.provider == "vendorA"
    assert usage_event.tokens_in == 500
    assert usage_event.tokens_out == 300
    assert usage_event.event_type == "test_direct"
    assert usage_event.metadata == {"test": "direct_creation"}

    # Verify cost calculation
    # (500 + 300) / 1000 * 0.002 = 0.001600
    expected_cost = Decimal("0.001600")
    assert usage_event.cost_usd == expected_cost

    # Verify it's actually in the database
    db_event = db_session.query(UsageEvent).filter(
        UsageEvent.id == usage_event.id
    ).first()
    assert db_event is not None
    assert db_event.cost_usd == expected_cost


@pytest.mark.integration
def test_cost_calculation_precision(
    db_session: Session,
    test_tenant: Tenant,
    test_agent: Agent,
    test_session: SessionModel
):
    """
    Integration test: Cost calculation maintains 6 decimal precision

    Ensures that fractional costs are calculated correctly to avoid
    rounding errors in billing.
    """

    # Test case with fractional result
    usage_event = create_usage_event(
        db=db_session,
        tenant_id=test_tenant.id,
        agent_id=test_agent.id,
        session_id=test_session.id,
        provider="vendorA",
        tokens_in=123,
        tokens_out=456,
        event_type="precision_test"
    )

    # Expected: (123 + 456) / 1000 * 0.002 = 0.001158
    expected_cost = Decimal("0.001158")
    assert usage_event.cost_usd == expected_cost

    # Verify precision is maintained in database
    db_event = db_session.query(UsageEvent).filter(
        UsageEvent.id == usage_event.id
    ).first()

    # Convert to string to verify exact decimal places
    cost_str = str(db_event.cost_usd)
    assert cost_str == "0.001158"
