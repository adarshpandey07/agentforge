"""API keys router: plaintext key returned exactly once at creation."""
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.core.security import generate_api_key
from app.models import ApiKey, User
from app.schemas.content import ApiKeyCreate, ApiKeyCreated, ApiKeyRead, ApiKeyUpdate
from app.services.audit import record_audit
from app.services.crud_base import CRUDService

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

_service: CRUDService = CRUDService(ApiKey, search_fields=("name", "prefix"))


@router.get("", response_model=list[ApiKeyRead])
async def list_api_keys(
    q: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    return await _service.list(db, tenant_id=user.tenant_id, q=q, skip=skip, limit=limit)


@router.post("", response_model=ApiKeyCreated, status_code=201)
async def create_api_key(
    payload: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
) -> Any:
    plaintext, prefix, hashed = generate_api_key()
    obj = await _service.create(
        db,
        tenant_id=user.tenant_id,
        data={"name": payload.name, "scopes": payload.scopes, "hashed_key": hashed, "prefix": prefix},
    )
    await record_audit(db, user=user, action="create", resource="api_key", resource_id=obj.id)
    read = ApiKeyRead.model_validate(obj)
    return ApiKeyCreated(**read.model_dump(), api_key=plaintext)


@router.patch("/{key_id}", response_model=ApiKeyRead)
async def update_api_key(
    key_id: str,
    payload: ApiKeyUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
) -> Any:
    obj = await _service.get(db, tenant_id=user.tenant_id, item_id=key_id)
    obj = await _service.update(db, obj=obj, data=payload.model_dump(exclude_unset=True, exclude_none=True))
    await record_audit(db, user=user, action="update", resource="api_key", resource_id=key_id)
    return obj


@router.delete("/{key_id}", status_code=204)
async def delete_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
) -> None:
    obj = await _service.get(db, tenant_id=user.tenant_id, item_id=key_id)
    await _service.delete(db, obj=obj)
    await record_audit(db, user=user, action="delete", resource="api_key", resource_id=key_id)
