"""Business models: clients, projects, agents, workflows, deployments, templates."""
from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin, UUIDMixin


class Client(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    business_type: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    contact_email: Mapped[str] = mapped_column(String(320), default="", nullable=False)
    phone: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    projects: Mapped[list["Project"]] = relationship(back_populates="client")


class Project(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "projects"

    client_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("clients.id", ondelete="SET NULL"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    client: Mapped["Client | None"] = relationship(back_populates="projects")
    agents: Mapped[list["Agent"]] = relationship(back_populates="project")


class Agent(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "agents"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    spec: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)

    project: Mapped["Project"] = relationship(back_populates="agents")
    workflows: Mapped[list["Workflow"]] = relationship(back_populates="agent")


class Workflow(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "workflows"

    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    graph: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    agent: Mapped["Agent"] = relationship(back_populates="workflows")


class Deployment(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "deployments"

    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    mode: Mapped[str] = mapped_column(String(20), default="docker", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    url: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    artifact: Mapped[str] = mapped_column(Text, default="", nullable=False)


class Template(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "templates"

    tenant_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=True
    )
    business_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    spec: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
