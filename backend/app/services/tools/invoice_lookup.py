"""
Invoice Lookup Tool with Company-Specific Data
"""
from typing import Dict, Any, List
from app.services.tools.base import Tool, ToolParameter


class InvoiceLookupTool(Tool):
    """Mock invoice lookup tool with company-specific data isolation"""

    # Company-specific invoice data - completely separated
    COMPANY_INVOICES = {
        # TechCorp invoices - Software/SaaS company
        "techcorp": {
            "INV-TC-001": {
                "id": "INV-TC-001",
                "amount": 15000.00,
                "status": "paid",
                "due_date": "2025-01-15",
                "customer": "Acme Solutions Inc",
                "description": "Annual Enterprise License - Q1 2025",
                "payment_date": "2025-01-10"
            },
            "INV-TC-002": {
                "id": "INV-TC-002",
                "amount": 8500.00,
                "status": "pending",
                "due_date": "2025-02-01",
                "customer": "StartupHub Ltd",
                "description": "Professional Plan - 50 seats",
                "payment_date": None
            },
            "INV-TC-003": {
                "id": "INV-TC-003",
                "amount": 3200.00,
                "status": "overdue",
                "due_date": "2024-12-15",
                "customer": "Global Tech Partners",
                "description": "Consulting Services - November 2024",
                "payment_date": None
            },
            "INV-TC-004": {
                "id": "INV-TC-004",
                "amount": 25000.00,
                "status": "paid",
                "due_date": "2025-01-20",
                "customer": "Enterprise Corp",
                "description": "Custom Development - Phase 1",
                "payment_date": "2025-01-18"
            },
            "INV-TC-005": {
                "id": "INV-TC-005",
                "amount": 12000.00,
                "status": "pending",
                "due_date": "2025-02-10",
                "customer": "MidSize Business Inc",
                "description": "Premium Support Package - Q1 2025",
                "payment_date": None
            },
            "INV-TC-006": {
                "id": "INV-TC-006",
                "amount": 5500.00,
                "status": "overdue",
                "due_date": "2024-11-30",
                "customer": "SmallBiz LLC",
                "description": "Integration Services",
                "payment_date": None
            }
        },

        # HealthFirst invoices - Healthcare company
        "healthfirst": {
            "INV-HF-001": {
                "id": "INV-HF-001",
                "amount": 45000.00,
                "status": "paid",
                "due_date": "2025-01-10",
                "customer": "City General Hospital",
                "description": "Medical Equipment Supply - December 2024",
                "payment_date": "2025-01-08"
            },
            "INV-HF-002": {
                "id": "INV-HF-002",
                "amount": 28500.00,
                "status": "pending",
                "due_date": "2025-02-05",
                "customer": "Wellness Clinic Network",
                "description": "Pharmaceutical Supplies - January 2025",
                "payment_date": None
            },
            "INV-HF-003": {
                "id": "INV-HF-003",
                "amount": 12750.00,
                "status": "overdue",
                "due_date": "2024-12-20",
                "customer": "Community Health Center",
                "description": "Diagnostic Equipment Maintenance",
                "payment_date": None
            },
            "INV-HF-004": {
                "id": "INV-HF-004",
                "amount": 67000.00,
                "status": "paid",
                "due_date": "2025-01-25",
                "customer": "Regional Medical Center",
                "description": "MRI Machine Installation",
                "payment_date": "2025-01-22"
            },
            "INV-HF-005": {
                "id": "INV-HF-005",
                "amount": 19200.00,
                "status": "pending",
                "due_date": "2025-02-15",
                "customer": "Private Practice Group",
                "description": "Medical Software Licensing - Annual",
                "payment_date": None
            },
            "INV-HF-006": {
                "id": "INV-HF-006",
                "amount": 8900.00,
                "status": "overdue",
                "due_date": "2024-11-15",
                "customer": "Dental Associates",
                "description": "Specialized Equipment Rental",
                "payment_date": None
            },
            "INV-HF-007": {
                "id": "INV-HF-007",
                "amount": 34000.00,
                "status": "paid",
                "due_date": "2025-01-12",
                "customer": "Emergency Care Facility",
                "description": "Emergency Response Equipment",
                "payment_date": "2025-01-11"
            }
        }
    }

    @property
    def name(self) -> str:
        return "invoice_lookup"

    @property
    def description(self) -> str:
        return "Look up invoice details by invoice ID"

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="invoice_id", type="string", description="Invoice ID", required=True)
        ]

    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        invoice_id = params.get("invoice_id")

        # Get company key from context
        company_key = context.get("company_key")

        if not company_key:
            return {
                "success": False,
                "error": "Unable to determine company context. Please ensure tenant has a company_key configured."
            }

        # Get company-specific invoices
        company_invoices = self.COMPANY_INVOICES.get(company_key, {})

        if not company_invoices:
            return {
                "success": False,
                "error": f"No invoice data available for company: {company_key}"
            }

        invoice = company_invoices.get(invoice_id)

        if not invoice:
            # List available invoices for this company
            available = list(company_invoices.keys())
            return {
                "success": False,
                "error": f"Invoice {invoice_id} not found. Available invoices: {', '.join(available[:5])}"
            }

        return {"success": True, "invoice": invoice}
