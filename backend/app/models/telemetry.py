"""Telemetry models: conversations, messages, llm_calls, tool_calls."""
from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin, UUIDMixin


class Conversation(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "conversations"

    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    session_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="web", nullable=False)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", order_by="Message.created_at"
    )


class Message(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class LlmCall(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "llm_calls"

    agent_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    conversation_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ToolCall(UUIDMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "tool_calls"

    agent_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    conversation_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    input: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    output: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str] = mapped_column(Text, default="", nullable=False)
