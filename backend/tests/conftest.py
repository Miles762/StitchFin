"""
Pytest configuration and fixtures for integration and unit tests
"""
import pytest
import asyncio
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import uuid

from app.utils.database import Base
from app.models.tenant import Tenant
from app.models.agent import Agent
from app.models.session import Session as SessionModel
from app.models.usage import UsageEvent
from app.middleware.auth import generate_api_key


# Test database URL (use PostgreSQL-compatible test database)
# For SQLite, we need to handle UUID conversion
import os
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:password@localhost:5432/vocalbridge_test")


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def test_tenant(db_session: Session) -> Tenant:
    """Create a test tenant"""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Test Tenant",
        company_key="test-corp",
        api_key=generate_api_key()
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    return tenant


@pytest.fixture(scope="function")
def test_agent(db_session: Session, test_tenant: Tenant) -> Agent:
    """Create a test agent"""
    agent = Agent(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Test Agent",
        primary_provider="vendorA",
        fallback_provider="vendorB",
        system_prompt="You are a helpful test assistant.",
        enabled_tools=[]
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    return agent


@pytest.fixture(scope="function")
def test_session(db_session: Session, test_tenant: Tenant, test_agent: Agent) -> SessionModel:
    """Create a test conversation session"""
    session = SessionModel(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        agent_id=test_agent.id,
        customer_id="test-customer-001",
        channel="chat",
        metadata={}
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    return session


@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
