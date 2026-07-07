"""Agents CRUD router + chat and simulate endpoints."""
from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.crud_factory import build_crud_router
from app.core.deps import get_current_user, get_db
from app.models import Agent, User
from app.schemas.business import (
    AgentCreate,
    AgentRead,
    AgentUpdate,
    ChatRequest,
    ChatResponse,
    SimulateRequest,
)
from app.services import ai_bridge
from app.services.chat import chat_with_agent

router, service = build_crud_router(
    prefix="/agents",
    tag="agents",
    resource="agent",
    model=Agent,
    read_schema=AgentRead,
    create_schema=AgentCreate,
    update_schema=AgentUpdate,
    search_fields=("name", "description", "status"),
)


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat(
    agent_id: str,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatResponse:
    """Run one chat turn against the agent via the AI runtime."""
    agent = await service.get(db, tenant_id=user.tenant_id, item_id=agent_id)
    result = await chat_with_agent(
        db,
        user=user,
        agent=agent,
        message=payload.message,
        session_id=payload.session_id,
        channel=payload.channel,
    )
    return ChatResponse(**result)


@router.post("/{agent_id}/simulate")
async def simulate(
    agent_id: str,
    payload: SimulateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Run an automated evaluation scenario against the agent spec."""
    agent = await service.get(db, tenant_id=user.tenant_id, item_id=agent_id)
    report = await ai_bridge.simulate_agent(agent.spec or {}, payload.scenario, payload.turns)
    # flatten so clients read turns/scores/passed at top level (SimulationReport shape)
    return {**report, "agent_id": agent.id, "scenario": payload.scenario}
