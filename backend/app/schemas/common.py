"""Shared Pydantic bases."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base for schemas hydrated from SQLAlchemy objects."""

    model_config = ConfigDict(from_attributes=True)


class ReadBase(ORMModel):
    """Common read fields for every resource."""

    id: str
    created_at: datetime
    updated_at: datetime


class TenantReadBase(ReadBase):
    tenant_id: str
