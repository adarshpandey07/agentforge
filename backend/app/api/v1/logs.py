"""Observability endpoints: llm calls, tool calls, audit logs."""
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models import AuditLog, LlmCall, ToolCall, User
from app.schemas.content import AuditLogRead
from app.schemas.telemetry import LlmCallRead, ToolCallRead
from app.services.crud_base import CRUDService

router = APIRouter(tags=["logs"])

_llm_service: CRUDService = CRUDService(LlmCall, search_fields=("model", "provider"))
_tool_service: CRUDService = CRUDService(ToolCall, search_fields=("tool_name",))
_audit_service: CRUDService = CRUDService(AuditLog, search_fields=("action", "resource", "actor"))


@router.get("/logs/llm-calls", response_model=list[LlmCallRead])
async def list_llm_calls(
    q: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    agent_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    return await _llm_service.list(
        db, tenant_id=user.tenant_id, q=q, skip=skip, limit=limit, agent_id=agent_id
    )


@router.get("/logs/tool-calls", response_model=list[ToolCallRead])
async def list_tool_calls(
    q: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    agent_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    return await _tool_service.list(
        db, tenant_id=user.tenant_id, q=q, skip=skip, limit=limit, agent_id=agent_id
    )


@router.get("/audit-logs", response_model=list[AuditLogRead])
async def list_audit_logs(
    q: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    return await _audit_service.list(db, tenant_id=user.tenant_id, q=q, skip=skip, limit=limit)
