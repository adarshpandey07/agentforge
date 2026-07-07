"""Prompts CRUD router + version management and prompt testing."""
from typing import Any

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.crud_factory import build_crud_router
from app.core.deps import get_current_user, get_db, require_role
from app.core.exceptions import NotFoundError
from app.models import Prompt, PromptVersion, User
from app.schemas.content import (
    PromptCreate,
    PromptRead,
    PromptTestRequest,
    PromptUpdate,
    PromptVersionCreate,
    PromptVersionRead,
)
from app.services import ai_bridge
from app.services.audit import record_audit
from app.services.crud_base import CRUDService

router, service = build_crud_router(
    prefix="/prompts",
    tag="prompts",
    resource="prompt",
    model=Prompt,
    read_schema=PromptRead,
    create_schema=PromptCreate,
    update_schema=PromptUpdate,
    search_fields=("name", "description"),
)
# The generated create endpoint ignores the optional `content` field (no such
# model column); override behaviour by exposing versions explicitly below.

_version_service: CRUDService = CRUDService(PromptVersion, search_fields=())


@router.get("/{prompt_id}/versions", response_model=list[PromptVersionRead])
async def list_versions(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    """List all versions of a prompt (ascending)."""
    await service.get(db, tenant_id=user.tenant_id, item_id=prompt_id)
    stmt = (
        select(PromptVersion)
        .where(PromptVersion.tenant_id == user.tenant_id, PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version.asc())
    )
    return list((await db.execute(stmt)).scalars().all())


@router.post("/{prompt_id}/versions", response_model=PromptVersionRead, status_code=201)
async def create_version(
    prompt_id: str,
    payload: PromptVersionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
) -> Any:
    """Append a new version (auto-incremented number) to a prompt."""
    prompt = await service.get(db, tenant_id=user.tenant_id, item_id=prompt_id)
    stmt = select(func.max(PromptVersion.version)).where(PromptVersion.prompt_id == prompt.id)
    current = (await db.execute(stmt)).scalar() or 0
    version = PromptVersion(
        tenant_id=user.tenant_id,
        prompt_id=prompt.id,
        content=payload.content,
        version=current + 1,
        notes=payload.notes,
    )
    db.add(version)
    await record_audit(
        db, user=user, action="create", resource="prompt_version",
        resource_id=prompt.id, detail={"version": current + 1}, commit=False,
    )
    await db.commit()
    await db.refresh(version)
    return version


@router.post("/{prompt_id}/test")
async def test_prompt(
    prompt_id: str,
    payload: PromptTestRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Run a one-off test of a prompt version through the AI runtime."""
    prompt = await service.get(db, tenant_id=user.tenant_id, item_id=prompt_id)
    stmt = select(PromptVersion).where(PromptVersion.prompt_id == prompt.id)
    if payload.version is not None:
        stmt = stmt.where(PromptVersion.version == payload.version)
    else:
        stmt = stmt.order_by(PromptVersion.version.desc())
    version = (await db.execute(stmt)).scalars().first()
    if version is None:
        raise NotFoundError("Prompt has no versions to test")

    spec = {
        "version": 1,
        "name": f"Prompt test: {prompt.name}",
        "agents": [
            {"id": "tester", "role": "Tester", "system_prompt": version.content,
             "tools": [], "memory": ["session"], "model": "auto"}
        ],
        "workflow": {"nodes": [], "edges": []},
    }
    result = await ai_bridge.run_agent(
        spec=spec, message=payload.input, session_id=f"prompt-test-{prompt.id}", context=None
    )
    return {
        "prompt_id": prompt.id,
        "version": version.version,
        "input": payload.input,
        "reply": result.get("reply", ""),
        "tokens": result.get("tokens", {}),
        "cost": result.get("cost", 0.0),
        "stub": result.get("stub", False),
    }
