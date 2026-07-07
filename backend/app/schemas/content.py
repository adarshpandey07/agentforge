"""Schemas for prompts, knowledge bases, documents, tools, integrations, api keys, audit logs."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import TenantReadBase


# -- Prompts -----------------------------------------------------------------
class PromptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    project_id: str
    description: str = ""
    content: str | None = None  # optional initial version content


class PromptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class PromptVersionCreate(BaseModel):
    content: str = Field(min_length=1)
    notes: str = ""


class PromptVersionRead(TenantReadBase):
    prompt_id: str
    content: str
    version: int
    notes: str


class PromptRead(TenantReadBase):
    name: str
    project_id: str
    description: str
    versions: list[PromptVersionRead] = Field(default_factory=list)


class PromptTestRequest(BaseModel):
    input: str = "Hello"
    version: int | None = None


# -- Knowledge bases -----------------------------------------------------------
class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    project_id: str
    vector_store: str = "pgvector"
    embedding_model: str = "text-embedding-3-small"


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = None
    vector_store: str | None = None
    embedding_model: str | None = None


class KnowledgeBaseRead(TenantReadBase):
    name: str
    project_id: str
    vector_store: str
    embedding_model: str


class DocumentRead(TenantReadBase):
    kb_id: str
    name: str
    source_type: str
    status: str
    meta: dict[str, Any]


# -- Tools -----------------------------------------------------------------
class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: str = "builtin"
    description: str = ""
    config: dict[str, Any] = Field(default_factory=dict)


class ToolUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    config: dict[str, Any] | None = None


class ToolRead(TenantReadBase):
    name: str
    type: str
    description: str
    config: dict[str, Any]


# -- Integrations ---------------------------------------------------------------
class IntegrationCreate(BaseModel):
    provider: str = Field(min_length=1, max_length=100)
    name: str = ""
    credentials: dict[str, Any] = Field(default_factory=dict)
    status: str = "connected"


class IntegrationUpdate(BaseModel):
    provider: str | None = None
    name: str | None = None
    credentials: dict[str, Any] | None = None
    status: str | None = None


class IntegrationRead(TenantReadBase):
    provider: str
    name: str
    status: str
    # credentials intentionally omitted from read schema


# -- API keys -----------------------------------------------------------------
class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=list)


class ApiKeyUpdate(BaseModel):
    name: str | None = None
    scopes: list[str] | None = None
    is_active: bool | None = None


class ApiKeyRead(TenantReadBase):
    name: str
    prefix: str
    scopes: list[str]
    is_active: bool
    last_used_at: datetime | None


class ApiKeyCreated(ApiKeyRead):
    api_key: str  # plaintext, shown exactly once


# -- Audit logs ---------------------------------------------------------------
class AuditLogRead(TenantReadBase):
    actor: str
    action: str
    resource: str
    resource_id: str | None
    detail: dict[str, Any]
