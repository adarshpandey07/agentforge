"""Content models: prompts, prompt_versions, knowledge_bases, documents, tools, integrations."""
from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin, UUIDMixin


class Prompt(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "prompts"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    versions: Mapped[list["PromptVersion"]] = relationship(
        back_populates="prompt", order_by="PromptVersion.version", lazy="selectin"
    )


class PromptVersion(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "prompt_versions"

    prompt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("prompts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    prompt: Mapped["Prompt"] = relationship(back_populates="versions")


class KnowledgeBase(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "knowledge_bases"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    vector_store: Mapped[str] = mapped_column(String(50), default="pgvector", nullable=False)
    embedding_model: Mapped[str] = mapped_column(
        String(100), default="text-embedding-3-small", nullable=False
    )

    documents: Mapped[list["Document"]] = relationship(back_populates="knowledge_base")


class Document(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "documents"

    kb_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), default="file", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="documents")


class Tool(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "tools"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="builtin", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class Integration(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "integrations"

    provider: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    credentials: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="connected", nullable=False)
