"""Templates CRUD + catalog + one-click instantiate."""
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.core.exceptions import NotFoundError
from app.models import Template, User
from app.schemas.business import (
    GenerateResponse,
    InstantiateRequest,
    TemplateCreate,
    TemplateRead,
    TemplateUpdate,
)
from app.services import ai_bridge
from app.services.audit import record_audit
from app.services.generate import persist_spec

router = APIRouter(prefix="/templates", tags=["templates"])


def _visible_templates_stmt(tenant_id: str):
    return select(Template).where(
        or_(Template.is_public.is_(True), Template.tenant_id == tenant_id)
    )


@router.get("/catalog")
async def catalog(user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    """Built-in business template catalog served by the AI engine."""
    return ai_bridge.list_templates()


@router.get("", response_model=list[TemplateRead])
async def list_templates_endpoint(
    q: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    """List public templates plus the tenant's own."""
    stmt = _visible_templates_stmt(user.tenant_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Template.name.ilike(like), Template.business_type.ilike(like)))
    stmt = stmt.order_by(Template.created_at.desc()).offset(skip).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template_endpoint(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    stmt = _visible_templates_stmt(user.tenant_id).where(Template.id == template_id)
    template = (await db.execute(stmt)).scalars().first()
    if template is None:
        raise NotFoundError(f"Template {template_id} not found")
    return template


@router.post("", response_model=TemplateRead, status_code=201)
async def create_template(
    payload: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
) -> Any:
    template = Template(tenant_id=user.tenant_id, **payload.model_dump(exclude_unset=True))
    db.add(template)
    await db.commit()
    await db.refresh(template)
    await record_audit(db, user=user, action="create", resource="template", resource_id=template.id)
    return template


@router.patch("/{template_id}", response_model=TemplateRead)
async def update_template(
    template_id: str,
    payload: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
) -> Any:
    stmt = select(Template).where(Template.id == template_id, Template.tenant_id == user.tenant_id)
    template = (await db.execute(stmt)).scalars().first()
    if template is None:
        raise NotFoundError(f"Template {template_id} not found")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(template, field, value)
    db.add(template)
    await db.commit()
    await db.refresh(template)
    await record_audit(db, user=user, action="update", resource="template", resource_id=template.id)
    return template


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
) -> None:
    stmt = select(Template).where(Template.id == template_id, Template.tenant_id == user.tenant_id)
    template = (await db.execute(stmt)).scalars().first()
    if template is None:
        raise NotFoundError(f"Template {template_id} not found")
    await db.delete(template)
    await db.commit()
    await record_audit(db, user=user, action="delete", resource="template", resource_id=template_id)


@router.post("/{template_id}/instantiate", response_model=GenerateResponse, status_code=201)
async def instantiate_template(
    template_id: str,
    payload: InstantiateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
) -> Any:
    """Clone a template's AgentSpec into a new project + agent + workflow + prompts."""
    stmt = _visible_templates_stmt(user.tenant_id).where(Template.id == template_id)
    template = (await db.execute(stmt)).scalars().first()
    if template is None:
        raise NotFoundError(f"Template {template_id} not found")

    spec: dict[str, Any] = dict(template.spec or {})
    spec.update(payload.customizations or {})
    result = await persist_spec(
        db, user=user, spec=spec, client_id=payload.client_id,
        project_name=spec.get("name", template.name),
    )
    return GenerateResponse(**result)
