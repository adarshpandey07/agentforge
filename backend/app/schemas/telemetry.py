"""Schemas for conversations, messages, llm calls, tool calls, analytics."""
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import TenantReadBase


class MessageRead(TenantReadBase):
    conversation_id: str
    role: str
    content: str
    tokens: int
    cost: float


class ConversationRead(TenantReadBase):
    agent_id: str
    session_id: str
    channel: str


class LlmCallRead(TenantReadBase):
    agent_id: str | None
    conversation_id: str | None
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    cost: float
    latency_ms: int


class ToolCallRead(TenantReadBase):
    agent_id: str | None
    conversation_id: str | None
    tool_name: str
    input: dict[str, Any]
    output: dict[str, Any]
    duration_ms: int
    error: str


class AnalyticsOverview(BaseModel):
    clients: int = 0
    projects: int = 0
    agents: int = 0
    conversations: int = 0
    messages: int = 0
    llm_calls: int = 0
    total_cost: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    tokens: int = 0
    deployments: int = 0
    extra: dict[str, Any] = Field(default_factory=dict)
