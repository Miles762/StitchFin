"""
Seed script - creates demo data
Creates 2 tenants with 3 agents each
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.database import SessionLocal
from app.models.tenant import Tenant
from app.models.agent import Agent
from app.middleware.auth import generate_api_key


def seed_data():
    """Seed the database with demo data"""
    db = SessionLocal()

    try:
        print("\\n" + "="*60)
        print("SEEDING VOCALBRIDGE OPS DATABASE")
        print("="*60 + "\\n")

        # Create Tenant 1: TechCorp (Software/SaaS Company)
        tenant1_key = generate_api_key()
        tenant1 = Tenant(
            name="TechCorp",
            company_key="techcorp",
            api_key=tenant1_key
        )
        db.add(tenant1)
        db.flush()

        print(f"✓ Created Tenant: TechCorp (Software/SaaS)")
        print(f"  API Key: {tenant1_key}")

        # Agents for TechCorp - Software/SaaS focused
        agent1_1 = Agent(
            tenant_id=tenant1.id,
            name="Customer Support Bot",
            primary_provider="vendorA",
            fallback_provider="vendorB",
            system_prompt="You are a helpful customer support agent for TechCorp, a software company. Help customers with their software licenses, subscriptions, and technical issues. Be friendly and professional.",
            enabled_tools=["invoice_lookup"],
            config={}
        )

        agent1_2 = Agent(
            tenant_id=tenant1.id,
            name="Sales Assistant",
            primary_provider="vendorB",
            fallback_provider=None,
            system_prompt="You are a sales assistant for TechCorp. Help customers find the right software plans and services. Explain features and pricing clearly.",
            enabled_tools=["invoice_lookup"],
            config={}
        )

        agent1_3 = Agent(
            tenant_id=tenant1.id,
            name="Billing Support",
            primary_provider="vendorA",
            fallback_provider="vendorB",
            system_prompt="You are a billing support specialist for TechCorp. Handle invoice inquiries, payment questions, and account billing issues. Be precise and helpful.",
            enabled_tools=["invoice_lookup"],
            config={}
        )

        db.add_all([agent1_1, agent1_2, agent1_3])
        print(f"  ✓ Created 3 agents")

        # Create Tenant 2: HealthFirst (Healthcare Company)
        tenant2_key = generate_api_key()
        tenant2 = Tenant(
            name="HealthFirst",
            company_key="healthfirst",
            api_key=tenant2_key
        )
        db.add(tenant2)
        db.flush()

        print(f"\\n✓ Created Tenant: HealthFirst (Healthcare)")
        print(f"  API Key: {tenant2_key}")

        # Agents for HealthFirst - Healthcare focused
        agent2_1 = Agent(
            tenant_id=tenant2.id,
            name="Medical Equipment Support",
            primary_provider="vendorB",
            fallback_provider="vendorA",
            system_prompt="You help healthcare providers with medical equipment orders, maintenance, and support. Be professional and precise with medical terminology.",
            enabled_tools=["invoice_lookup"],
            config={}
        )

        agent2_2 = Agent(
            tenant_id=tenant2.id,
            name="Billing & Insurance Assistant",
            primary_provider="vendorA",
            fallback_provider=None,
            system_prompt="You handle billing inquiries for medical equipment and services. Help with invoices, insurance claims, and payment details. Be accurate and empathetic.",
            enabled_tools=["invoice_lookup"],
            config={}
        )

        agent2_3 = Agent(
            tenant_id=tenant2.id,
            name="Supply Chain Coordinator",
            primary_provider="vendorB",
            fallback_provider="vendorA",
            system_prompt="You assist with medical supply orders, delivery tracking, and inventory management. Provide clear information about orders and invoices.",
            enabled_tools=["invoice_lookup"],
            config={}
        )

        db.add_all([agent2_1, agent2_2, agent2_3])
        print(f"  ✓ Created 3 agents")

        db.commit()

        print("\\n" + "="*60)
        print("SEED DATA CREATED SUCCESSFULLY!")
        print("="*60)

        print("\\n📋 TENANT CREDENTIALS:\\n")
        print(f"Tenant 1: TechCorp (Software/SaaS)")
        print(f"  Company Key: techcorp")
        print(f"  API Key: {tenant1_key}\\n")

        print(f"Tenant 2: HealthFirst (Healthcare)")
        print(f"  Company Key: healthfirst")
        print(f"  API Key: {tenant2_key}\\n")

        print("💡 Use these API keys in the X-API-Key header for API requests")
        print("💡 Or use them to login in the frontend dashboard\\n")

    except Exception as e:
        db.rollback()
        print(f"\\n❌ Error seeding database: {e}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
