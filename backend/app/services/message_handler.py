"""
Message handling service - orchestrates vendor calls, billing, and tools
"""
import time
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.session import Session as SessionModel, Message
from app.models.agent import Agent
from app.services.vendors.base import VendorRequest
from app.services.reliability.resilient_caller import ResilientVendorCaller
from app.services.billing.metering import create_usage_event
from app.services.idempotency import IdempotencyService
from app.services.tools.executor import ToolExecutor
from app.schemas.session import MessageResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MessageHandler:
    """
    Handles message processing with vendor calls, billing, and tool execution
    """

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        session: SessionModel,
        correlation_id: Optional[str]
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.session = session
        self.correlation_id = correlation_id

        # Load agent
        self.agent = db.query(Agent).filter(Agent.id == session.agent_id).first()

    async def handle_message(
        self,
        user_message: str,
        idempotency_key: Optional[str] = None
    ) -> MessageResponse:
        """
        Process user message and return assistant response
        """
        # Check idempotency
        if idempotency_key:
            idempotency_service = IdempotencyService(self.db, self.tenant_id)
            cached_response = idempotency_service.get_cached_response(idempotency_key)
            if cached_response:
                return MessageResponse(**cached_response)

        start_time = time.time()

        # Create user message
        user_msg = Message(
            session_id=self.session.id,
            role="user",
            content=user_message,
            correlation_id=self.correlation_id
        )
        self.db.add(user_msg)
        self.db.commit()

        # Prepare vendor request
        vendor_request = VendorRequest(
            system_prompt=self.agent.system_prompt,
            user_message=user_message
        )

        # Call vendor with resilience
        caller = ResilientVendorCaller(
            tenant_id=str(self.tenant_id),
            session_id=str(self.session.id),
            correlation_id=self.correlation_id,
            db=self.db
        )

        vendor_response = await caller.call_with_fallback(
            primary_provider=self.agent.primary_provider,
            fallback_provider=self.agent.fallback_provider,
            request=vendor_request
        )

        total_latency = int((time.time() - start_time) * 1000)

        # Check for tool calls
        tools_called = []
        response_text = vendor_response.text

        # Check if message contains invoice-related keywords or invoice ID patterns
        has_invoice_keyword = any(keyword in user_message.lower() for keyword in ["invoice", "inv-", "inv "])

        if self.agent.enabled_tools and has_invoice_keyword:
            # Simple tool detection (in production, use function calling)
            import re

            # Extract invoice ID from message
            # Supports formats: "INV-TC-001", "INV-HF-007", "inv-tc-1", etc.
            invoice_id = None

            # Try to find INV-XX-XXX format (company-specific invoices)
            # Matches: INV-TC-001, INV-HF-007, etc.
            inv_match = re.search(r'INV-[A-Z]+-\d+', user_message, re.IGNORECASE)
            if inv_match:
                invoice_id = inv_match.group(0).upper()
            else:
                # Try legacy INV-XXX format
                inv_match = re.search(r'INV-?\d+', user_message, re.IGNORECASE)
                if inv_match:
                    invoice_id = inv_match.group(0).upper()
                    if '-' not in invoice_id:
                        # Add dash if missing (e.g., "INV001" -> "INV-001")
                        invoice_id = re.sub(r'(INV)(\d+)', r'\1-\2', invoice_id)
                else:
                    # Try to find just numbers after "invoice", "inv", "order", "id"
                    num_match = re.search(r'(?:invoice|inv|order|id)\s*[:\-#]?\s*(\d+)', user_message, re.IGNORECASE)
                    if num_match:
                        num = num_match.group(1).zfill(3)  # Pad to 3 digits
                        invoice_id = f"INV-{num}"

            # Only call tool if invoice ID was found
            if invoice_id:
                tool_executor = ToolExecutor(self.db, self.tenant_id, self.agent.id, self.session.id)
                tool_result = await tool_executor.execute_tool(
                    "invoice_lookup",
                    {"invoice_id": invoice_id}
                )
            else:
                tool_result = None

            if tool_result:
                tools_called.append("invoice_lookup")
                if tool_result.get("success"):
                    invoice = tool_result.get('invoice')
                    # Replace AI response with tool-enhanced response
                    status_emoji = {
                        'paid': '✅',
                        'pending': '⏳',
                        'overdue': '⚠️'
                    }.get(invoice['status'], '📄')

                    response_text = (
                        f"I found the invoice you requested:\n\n"
                        f"📄 Invoice ID: {invoice['id']}\n"
                        f"👤 Customer: {invoice.get('customer', 'N/A')}\n"
                        f"📝 Description: {invoice.get('description', 'N/A')}\n"
                        f"💰 Amount: ${invoice['amount']:,.2f}\n"
                        f"{status_emoji} Status: {invoice['status'].upper()}\n"
                        f"📅 Due Date: {invoice['due_date']}"
                    )

                    if invoice.get('payment_date'):
                        response_text += f"\n💳 Paid On: {invoice['payment_date']}"
                else:
                    # Invoice not found
                    error_msg = tool_result.get("error", "Invoice not found")
                    response_text = f"❌ {error_msg}"

        # Create assistant message
        assistant_msg = Message(
            session_id=self.session.id,
            role="assistant",
            content=response_text,
            provider_used=self.agent.primary_provider,  # Track which vendor was used
            tokens_in=vendor_response.tokens_in,
            tokens_out=vendor_response.tokens_out,
            latency_ms=total_latency,
            tools_called=tools_called,
            correlation_id=self.correlation_id
        )
        self.db.add(assistant_msg)
        self.db.commit()
        self.db.refresh(assistant_msg)

        # Create usage event
        usage_event = create_usage_event(
            db=self.db,
            tenant_id=self.tenant_id,
            agent_id=self.agent.id,
            session_id=self.session.id,
            message_id=assistant_msg.id,
            provider=self.agent.primary_provider,
            tokens_in=vendor_response.tokens_in,
            tokens_out=vendor_response.tokens_out
        )

        # Build response
        response_data = {
            "id": assistant_msg.id,
            "session_id": assistant_msg.session_id,
            "role": assistant_msg.role,
            "content": assistant_msg.content,
            "provider_used": assistant_msg.provider_used,
            "tokens_in": assistant_msg.tokens_in,
            "tokens_out": assistant_msg.tokens_out,
            "latency_ms": assistant_msg.latency_ms,
            "tools_called": assistant_msg.tools_called,
            "correlation_id": assistant_msg.correlation_id,
            "cost_usd": usage_event.cost_usd,
            "created_at": assistant_msg.created_at
        }

        # Cache for idempotency
        if idempotency_key:
            idempotency_service.cache_response(idempotency_key, response_data)

        return MessageResponse(**response_data)
