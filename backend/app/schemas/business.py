"""Schemas for clients, projects, agents, workflows, deployments, templates, generate."""
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ReadBase, TenantReadBase


# -- Clients ---------------------------------------------------------------
class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    business_type: str = ""
    contact_email: str = ""
    phone: str = ""
    notes: str = ""
    meta: dict[str, Any] = Field(default_factory=dict)


class ClientUpdate(BaseModel):
    name: str | None = None
    business_type: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    notes: str | None = None
    meta: dict[str, Any] | None = None


class ClientRead(TenantReadBase):
    name: str
    business_type: str
    contact_email: str
    phone: str
    notes: str
    meta: dict[str, Any]


# -- Projects ----------------------------------------------------------------
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    client_id: str | None = None
    description: str = ""
    status: str = "active"


class ProjectUpdate(BaseModel):
    name: str | None = None
    client_id: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectRead(TenantReadBase):
    name: str
    client_id: str | None
    description: str
    status: str


# -- Agents ------------------------------------------------------------------
class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    project_id: str
    description: str = ""
    spec: dict[str, Any] = Field(default_factory=dict)
    status: str = "draft"


class AgentUpdate(BaseModel):
    name: str | None = None
    project_id: str | None = None
    description: str | None = None
    spec: dict[str, Any] | None = None
    status: str | None = None


class AgentRead(TenantReadBase):
    name: str
    project_id: str
    description: str
    spec: dict[str, Any]
    status: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = "default"
    channel: str = "web"


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    conversation_id: str
    tokens: dict[str, Any] = Field(default_factory=dict)
    cost: float = 0.0
    stub: bool = False


class SimulateRequest(BaseModel):
    scenario: str = Field(min_length=1)
    turns: int = Field(default=5, ge=1, le=20)


# -- Workflows ---------------------------------------------------------------
class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    agent_id: str
    graph: dict[str, Any] = Field(default_factory=dict)
    version: int = 1


class WorkflowUpdate(BaseModel):
    name: str | None = None
    graph: dict[str, Any] | None = None
    version: int | None = None


class WorkflowRead(TenantReadBase):
    name: str
    agent_id: str
    graph: dict[str, Any]
    version: int


# -- Deployments ---------------------------------------------------------------
class DeploymentCreate(BaseModel):
    agent_id: str
    mode: str = Field(default="docker", pattern="^(docker|cloud|vps|local)$")


class DeploymentUpdate(BaseModel):
    status: str | None = None
    url: str | None = None


class DeploymentRead(TenantReadBase):
    agent_id: str
    mode: str
    status: str
    url: str
    artifact: str


# -- Templates ---------------------------------------------------------------
class TemplateCreate(BaseModel):
    business_type: str
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    spec: dict[str, Any] = Field(default_factory=dict)
    is_public: bool = True


class TemplateUpdate(BaseModel):
    business_type: str | None = None
    name: str | None = None
    description: str | None = None
    spec: dict[str, Any] | None = None
    is_public: bool | None = None


class TemplateRead(ReadBase):
    tenant_id: str | None
    business_type: str
    name: str
    description: str
    spec: dict[str, Any]
    is_public: bool


class InstantiateRequest(BaseModel):
    client_id: str
    customizations: dict[str, Any] = Field(default_factory=dict)


# -- Generate ------------------------------------------------------------------
class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    business_type: str | None = None
    client_id: str | None = None


class GenerateResponse(BaseModel):
    spec: dict[str, Any]
    project_id: str
    agent_id: str
    workflow_id: str
    prompt_ids: list[str] = Field(default_factory=list)
