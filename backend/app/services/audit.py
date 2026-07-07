"""Audit trail service: records every mutation into audit_logs."""
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, User


async def record_audit(
    db: AsyncSession,
    *,
    user: User,
    action: str,
    resource: str,
    resource_id: str | None = None,
    detail: dict[str, Any] | None = None,
    commit: bool = True,
) -> AuditLog:
    """Write an audit_logs row for a mutation performed by `user`."""
    entry = AuditLog(
        tenant_id=user.tenant_id,
        actor=user.email,
        action=action,
        resource=resource,
        resource_id=resource_id,
        detail=detail or {},
    )
    db.add(entry)
    if commit:
        await db.commit()
    return entry
