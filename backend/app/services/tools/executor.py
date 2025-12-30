"""
Tool executor with audit logging
"""
import time
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.tool import ToolExecution
from app.services.tools.invoice_lookup import InvoiceLookupTool


class ToolExecutor:
    """Executes tools with audit logging"""

    TOOLS = {
        "invoice_lookup": InvoiceLookupTool()
    }

    def __init__(self, db: Session, tenant_id: UUID, agent_id: UUID, session_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.session_id = session_id

        # Load tenant to get company_key
        from app.models.tenant import Tenant
        self.tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        self.company_key = self.tenant.company_key if self.tenant else None

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        message_id: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute tool with audit"""
        tool = self.TOOLS.get(tool_name)
        if not tool:
            return None

        start_time = time.time()

        execution = ToolExecution(
            tenant_id=self.tenant_id,
            agent_id=self.agent_id,
            session_id=self.session_id,
            message_id=message_id,
            tool_name=tool_name,
            parameters=params,
            status="pending"
        )
        self.db.add(execution)
        self.db.flush()

        try:
            context = {
                "tenant_id": str(self.tenant_id),
                "agent_id": str(self.agent_id),
                "session_id": str(self.session_id),
                "company_key": self.company_key
            }
            result = await tool.execute(params, context)

            execution.status = "success"
            execution.result = result
            execution.latency_ms = int((time.time() - start_time) * 1000)
            self.db.commit()

            return result

        except Exception as e:
            execution.status = "error"
            execution.error_message = str(e)
            execution.latency_ms = int((time.time() - start_time) * 1000)
            self.db.commit()
            raise
