"""Tenancy models: tenants, users, api_keys, audit_logs."""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin, UUIDMixin


class Tenant(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="tenant", lazy="selectin")


class User(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="users", lazy="joined")


class ApiKey(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    scopes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "audit_logs"

    actor: Mapped[str] = mapped_column(String(320), nullable=False)
    action: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    resource: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
