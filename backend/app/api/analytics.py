"""
Analytics API endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from datetime import datetime, date
from typing import Optional
from decimal import Decimal

from app.models.tenant import Tenant
from app.models.agent import Agent
from app.models.session import Session
from app.models.usage import UsageEvent
from app.schemas.analytics import UsageAnalytics, ProviderStats, TopAgentsResponse, TopAgent
from app.utils.database import get_db
from app.middleware.auth import get_current_tenant

router = APIRouter()


@router.get("/usage", response_model=UsageAnalytics)
async def get_usage_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    tenant: Tenant = Depends(get_current_tenant),
    db: DBSession = Depends(get_db)
):
    """
    Get usage analytics for a date range
    """
    query = db.query(UsageEvent).filter(UsageEvent.tenant_id == tenant.id)

    if start_date:
        query = query.filter(UsageEvent.created_at >= start_date)
    if end_date:
        query = query.filter(UsageEvent.created_at <= end_date)

    usage_events = query.all()

    # Calculate totals
    total_sessions = db.query(func.count(func.distinct(UsageEvent.session_id))).filter(
        UsageEvent.tenant_id == tenant.id
    ).scalar() or 0

    total_tokens_in = sum(e.tokens_in for e in usage_events)
    total_tokens_out = sum(e.tokens_out for e in usage_events)
    total_cost = sum(e.cost_usd for e in usage_events)

    # Breakdown by provider
    provider_breakdown = {}
    for provider in ['vendorA', 'vendorB']:
        provider_events = [e for e in usage_events if e.provider == provider]
        if provider_events:
            provider_breakdown[provider] = ProviderStats(
                sessions=len(set(e.session_id for e in provider_events)),
                tokens_in=sum(e.tokens_in for e in provider_events),
                tokens_out=sum(e.tokens_out for e in provider_events),
                cost_usd=Decimal(sum(e.cost_usd for e in provider_events))
            )

    return UsageAnalytics(
        total_sessions=total_sessions,
        total_messages=len(usage_events),
        total_tokens_in=total_tokens_in,
        total_tokens_out=total_tokens_out,
        total_cost_usd=Decimal(total_cost),
        breakdown_by_provider=provider_breakdown
    )


@router.get("/top-agents", response_model=TopAgentsResponse)
async def get_top_agents(
    limit: int = Query(10, ge=1, le=50),
    tenant: Tenant = Depends(get_current_tenant),
    db: DBSession = Depends(get_db)
):
    """
    Get top agents by cost
    """
    results = db.query(
        Agent.id,
        Agent.name,
        func.count(func.distinct(UsageEvent.session_id)).label('total_sessions'),
        func.sum(UsageEvent.cost_usd).label('total_cost'),
        func.sum(UsageEvent.tokens_in + UsageEvent.tokens_out).label('total_tokens')
    ).join(
        UsageEvent, Agent.id == UsageEvent.agent_id
    ).filter(
        Agent.tenant_id == tenant.id
    ).group_by(
        Agent.id, Agent.name
    ).order_by(
        func.sum(UsageEvent.cost_usd).desc()
    ).limit(limit).all()

    agents = [
        TopAgent(
            agent_id=r[0],
            agent_name=r[1],
            total_sessions=r[2],
            total_cost_usd=Decimal(r[3] or 0),
            total_tokens=r[4] or 0
        )
        for r in results
    ]

    return TopAgentsResponse(agents=agents)
