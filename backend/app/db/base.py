"""Declarative base and shared model mixins."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Project-wide declarative base. dict/list annotations map to JSON."""

    type_annotation_map = {dict: JSON, list: JSON}


class UUIDMixin:
    """String(36) uuid4 primary key (portable across Postgres and SQLite)."""

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )


class TimestampMixin:
    """created_at / updated_at columns on every table."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class TenantMixin:
    """tenant_id FK for multi-tenant scoping of all domain tables."""

    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
