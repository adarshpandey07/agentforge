"""Chat service: runs an agent via the AI runtime and persists all telemetry."""
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Conversation, LlmCall, Message, ToolCall, User
from app.services import ai_bridge


async def _get_or_create_conversation(
    db: AsyncSession, *, tenant_id: str, agent_id: str, session_id: str, channel: str
) -> Conversation:
    stmt = select(Conversation).where(
        Conversation.tenant_id == tenant_id,
        Conversation.agent_id == agent_id,
        Conversation.session_id == session_id,
    )
    conversation = (await db.execute(stmt)).scalars().first()
    if conversation is None:
        conversation = Conversation(
            tenant_id=tenant_id, agent_id=agent_id, session_id=session_id, channel=channel
        )
        db.add(conversation)
        await db.flush()
    return conversation


async def chat_with_agent(
    db: AsyncSession,
    *,
    user: User,
    agent: Agent,
    message: str,
    session_id: str,
    channel: str = "web",
) -> dict[str, Any]:
    """Run one chat turn: persist user message, invoke runtime, persist reply,
    llm_calls and tool_calls with token/cost accounting."""
    tenant_id = user.tenant_id
    conversation = await _get_or_create_conversation(
        db, tenant_id=tenant_id, agent_id=agent.id, session_id=session_id, channel=channel
    )

    db.add(
        Message(
            tenant_id=tenant_id,
            conversation_id=conversation.id,
            role="user",
            content=message,
            tokens=max(1, len(message) // 4),
            cost=0.0,
        )
    )

    result = await ai_bridge.run_agent(
        spec=agent.spec or {},
        message=message,
        session_id=session_id,
        context={"tenant_id": tenant_id, "agent_id": agent.id, "user_id": user.id},
    )

    tokens: dict[str, Any] = result.get("tokens", {}) or {}
    total_cost = float(result.get("cost", 0.0) or 0.0)

    db.add(
        Message(
            tenant_id=tenant_id,
            conversation_id=conversation.id,
            role="assistant",
            content=str(result.get("reply", "")),
            tokens=int(tokens.get("completion", 0) or 0),
            cost=total_cost,
        )
    )

    for call in result.get("llm_calls", []) or []:
        db.add(
            LlmCall(
                tenant_id=tenant_id,
                agent_id=agent.id,
                conversation_id=conversation.id,
                model=str(call.get("model", "unknown")),
                provider=str(call.get("provider", "unknown")),
                prompt_tokens=int(call.get("prompt_tokens", 0) or 0),
                completion_tokens=int(call.get("completion_tokens", 0) or 0),
                cost=float(call.get("cost", 0.0) or 0.0),
                latency_ms=int(call.get("latency_ms", 0) or 0),
            )
        )

    for call in result.get("tool_calls", []) or []:
        db.add(
            ToolCall(
                tenant_id=tenant_id,
                agent_id=agent.id,
                conversation_id=conversation.id,
                tool_name=str(call.get("tool_name", call.get("name", "unknown"))),
                input=call.get("input", {}) or {},
                output=call.get("output", {}) or {},
                duration_ms=int(call.get("duration_ms", 0) or 0),
                error=str(call.get("error", "") or ""),
            )
        )

    await db.commit()

    return {
        "reply": str(result.get("reply", "")),
        "session_id": session_id,
        "conversation_id": conversation.id,
        "tokens": tokens,
        "cost": total_cost,
        "stub": bool(result.get("stub", False)),
    }
