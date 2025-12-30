"""
Multi-tenant authentication middleware
"""
import secrets
from typing import Optional
from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.utils.database import get_db
from app.middleware.error_handler import UnauthorizedException


def generate_api_key() -> str:
    """
    Generate a secure API key
    """
    return f"sk_{''.join(secrets.token_urlsafe(32))}"


def get_tenant_from_api_key(api_key: str, db: Session) -> Optional[Tenant]:
    """
    Get tenant by API key
    """
    return db.query(Tenant).filter(Tenant.api_key == api_key).first()


async def get_current_tenant(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Dependency to get current tenant from API key
    Ensures multi-tenant isolation
    """
    if not x_api_key:
        raise UnauthorizedException("API key is required")

    tenant = get_tenant_from_api_key(x_api_key, db)
    if not tenant:
        raise UnauthorizedException("Invalid API key")

    return tenant
