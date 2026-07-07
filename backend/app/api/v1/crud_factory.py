"""Factory producing tenant-scoped CRUD routers with audit logging.

Keeps every resource router thin and uniform: list (q/skip/limit), get,
create, update, delete — all scoped to the caller's tenant, with audit_logs
entries written on every mutation.
"""
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.db.base import Base
from app.models import User
from app.services.audit import record_audit
from app.services.crud_base import CRUDService


def build_crud_router(
    *,
    prefix: str,
    tag: str,
    resource: str,
    model: type[Base],
    read_schema: type[BaseModel],
    create_schema: type[BaseModel],
    update_schema: type[BaseModel],
    search_fields: tuple[str, ...] = ("name",),
    write_role: str = "member",
    delete_role: str = "admin",
) -> tuple[APIRouter, CRUDService]:
    """Build an APIRouter exposing standard CRUD for `model`. Returns
    (router, service) so callers can append custom endpoints."""
    router = APIRouter(prefix=prefix, tags=[tag])
    service: CRUDService = CRUDService(model, search_fields=search_fields)

    @router.get("", response_model=list[read_schema])
    async def list_items(
        q: str | None = Query(default=None, description="Search query"),
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=200),
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user),
    ) -> Any:
        return await service.list(db, tenant_id=user.tenant_id, q=q, skip=skip, limit=limit)

    @router.get("/{item_id}", response_model=read_schema)
    async def get_item(
        item_id: str,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user),
    ) -> Any:
        return await service.get(db, tenant_id=user.tenant_id, item_id=item_id)

    @router.post("", response_model=read_schema, status_code=201)
    async def create_item(
        payload: create_schema,  # type: ignore[valid-type]
        db: AsyncSession = Depends(get_db),
        user: User = Depends(require_role(write_role)),
    ) -> Any:
        obj = await service.create(
            db, tenant_id=user.tenant_id, data=payload.model_dump(exclude_unset=True)
        )
        await record_audit(db, user=user, action="create", resource=resource, resource_id=obj.id)
        return obj

    @router.patch("/{item_id}", response_model=read_schema)
    async def update_item(
        item_id: str,
        payload: update_schema,  # type: ignore[valid-type]
        db: AsyncSession = Depends(get_db),
        user: User = Depends(require_role(write_role)),
    ) -> Any:
        obj = await service.get(db, tenant_id=user.tenant_id, item_id=item_id)
        data = payload.model_dump(exclude_unset=True, exclude_none=True)
        obj = await service.update(db, obj=obj, data=data)
        await record_audit(
            db, user=user, action="update", resource=resource, resource_id=item_id,
            detail={"fields": sorted(data.keys())},
        )
        return obj

    @router.delete("/{item_id}", status_code=204)
    async def delete_item(
        item_id: str,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(require_role(delete_role)),
    ) -> None:
        obj = await service.get(db, tenant_id=user.tenant_id, item_id=item_id)
        await service.delete(db, obj=obj)
        await record_audit(db, user=user, action="delete", resource=resource, resource_id=item_id)

    return router, service
