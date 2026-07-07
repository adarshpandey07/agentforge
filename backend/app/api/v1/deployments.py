"""Deployments router: artifact generation + standard listing."""
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.models import Agent, Deployment, User
from app.schemas.business import DeploymentCreate, DeploymentRead, DeploymentUpdate
from app.services.audit import record_audit
from app.services.crud_base import CRUDService
from app.services.deployment import create_deployment

router = APIRouter(prefix="/deployments", tags=["deployments"])

_service: CRUDService = CRUDService(Deployment, search_fields=("mode", "status"))
_agent_service: CRUDService = CRUDService(Agent)


@router.get("", response_model=list[DeploymentRead])
async def list_deployments(
    q: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    return await _service.list(db, tenant_id=user.tenant_id, q=q, skip=skip, limit=limit)


@router.get("/{deployment_id}", response_model=DeploymentRead)
async def get_deployment(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    return await _service.get(db, tenant_id=user.tenant_id, item_id=deployment_id)


@router.post("", response_model=DeploymentRead, status_code=201)
async def create_deployment_endpoint(
    payload: DeploymentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
) -> Any:
    """Generate deploy artifacts (docker-compose) for an agent and record the deployment."""
    agent = await _agent_service.get(db, tenant_id=user.tenant_id, item_id=payload.agent_id)
    return await create_deployment(db, user=user, agent=agent, mode=payload.mode)


@router.patch("/{deployment_id}", response_model=DeploymentRead)
async def update_deployment(
    deployment_id: str,
    payload: DeploymentUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
) -> Any:
    obj = await _service.get(db, tenant_id=user.tenant_id, item_id=deployment_id)
    obj = await _service.update(db, obj=obj, data=payload.model_dump(exclude_unset=True, exclude_none=True))
    await record_audit(db, user=user, action="update", resource="deployment", resource_id=deployment_id)
    return obj


@router.delete("/{deployment_id}", status_code=204)
async def delete_deployment(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
) -> None:
    obj = await _service.get(db, tenant_id=user.tenant_id, item_id=deployment_id)
    await _service.delete(db, obj=obj)
    await record_audit(db, user=user, action="delete", resource="deployment", resource_id=deployment_id)
