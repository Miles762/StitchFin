"""
Tenant schemas
"""
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class TenantCreate(BaseModel):
    name: str


class TenantResponse(BaseModel):
    id: UUID
    name: str
    api_key: str
    created_at: datetime

    class Config:
        from_attributes = True


class TenantInfo(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True
