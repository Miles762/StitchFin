"""
Agent API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.models.tenant import Tenant
from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.utils.database import get_db
from app.middleware.auth import get_current_tenant
from app.middleware.error_handler import NotFoundException

router = APIRouter()


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """List all agents for the current tenant"""
    agents = db.query(Agent).filter(Agent.tenant_id == tenant.id).all()
    return agents


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    agent_data: AgentCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Create a new agent"""
    agent = Agent(
        tenant_id=tenant.id,
        name=agent_data.name,
        primary_provider=agent_data.primary_provider,
        fallback_provider=agent_data.fallback_provider,
        system_prompt=agent_data.system_prompt,
        enabled_tools=agent_data.enabled_tools,
        config=agent_data.config
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get agent by ID"""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.tenant_id == tenant.id
    ).first()

    if not agent:
        raise NotFoundException("Agent not found")

    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_data: AgentUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Update agent"""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.tenant_id == tenant.id
    ).first()

    if not agent:
        raise NotFoundException("Agent not found")

    # Update fields
    update_data = agent_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    db.commit()
    db.refresh(agent)

    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Delete agent"""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.tenant_id == tenant.id
    ).first()

    if not agent:
        raise NotFoundException("Agent not found")

    db.delete(agent)
    db.commit()

    return None
