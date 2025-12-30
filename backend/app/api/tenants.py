"""
Tenant API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantResponse
from app.utils.database import get_db
from app.middleware.auth import generate_api_key

router = APIRouter()


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new tenant and issue an API key
    """
    api_key = generate_api_key()

    tenant = Tenant(
        name=tenant_data.name,
        api_key=api_key
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return tenant
