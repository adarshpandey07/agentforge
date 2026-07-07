"""Agent runtime: run one message through an AgentSpec.

Public interface (contract):
    async run_agent(spec, message, session_id, context=None) ->
        {"reply", "llm_calls", "tool_calls", "tokens", "cost"}

Works end-to-end with ZERO API keys: when no provider key is configured (or
langgraph is missing) it produces a deterministic, useful stub reply derived
from the spec's prompts and tools, marked ``"stub": true``.
"""
from __future__ import annotations

import time
from typing import Any, Optional

from .memory import get_memory
from .multi_agent.supervisor import route_deterministic
from .router.model_router import estimate_cost, provider_available, select_model
from .tools.registry import TOOLS


def _est_tokens(*texts: str) -> int:
    return max(1, sum(len(t) for t in texts if t) // 4)


async def _run_stub(spec: dict, message: str, session_id: str,
                    context: Optional[dict], choice: dict, start: float) -> dict:
    """Deterministic no-key execution: route, run relevant tool stubs, reply."""
    agents = spec.get("agents", []) or []
    agent_id = route_deterministic(spec, message) if agents else "assistant"
    agent = next((a for a in agents if a.get("id") == agent_id), agents[0] if agents else {})
    role = agent.get("role", "Assistant")
    name = spec.get("name", "the agent")

    # Execute tool stubs the routed agent would plausibly use.
    tool_calls: list[dict] = []
    msg_l = (message or "").lower()
    tool_hints = {
        "booking": ("book", "appointment", "reserve", "schedule", "cancel", "table"),
        "faq_rag": ("what", "how", "when", "where", "price", "hour", "open", "?"),
        "twilio_sms": ("text me", "sms",),
        "whatsapp": ("whatsapp",),
    }
    for tool_name in (agent.get("tools") or [])[:3]:
        plugin = TOOLS.get(tool_name)
        if plugin is None:
            continue
        hints = tool_hints.get(tool_name)
        if hints is not None and not any(h in msg_l for h in hints):
            continue
        t0 = time.time()
        try:
            if tool_name == "faq_rag":
                result = await plugin.execute(query=message, kb_id=context.get("kb_id", "default") if context else "default")
            elif tool_name == "booking":
                result = await plugin.execute(action="check")
            else:
                result = await plugin.execute(action=f"handle: {message[:80]}")
            error = None
        except Exception as exc:  # tool stubs should never raise, but be safe
            result, error = {"stub": True, "error": str(exc)}, str(exc)
        tool_calls.append({
            "tool_name": tool_name, "input": {"message": message[:200]},
            "output": result, "duration_ms": int((time.time() - t0) * 1000),
            "error": error,
        })

    # Compose a deterministic, genuinely informative reply.
    prompt_head = (agent.get("system_prompt") or "").split(". ")[0][:220]
    tool_names = ", ".join(agent.get("tools") or []) or "no tools"
    rag_snippets = []
    for tc in tool_calls:
        if tc["tool_name"] == "faq_rag":
            for r in (tc["output"] or {}).get("results", [])[:2]:
                rag_snippets.append(r.get("text", "")[:180])
    reply_parts = [
        f"[stub reply — no LLM API key configured] {name} routed your message to the "
        f"'{role}' agent ({agent_id}).",
        f"That agent's instructions begin: \"{prompt_head}\".",
        f"It has access to: {tool_names}.",
    ]
    if rag_snippets:
        reply_parts.append("From the knowledge base it would ground its answer on: " +
                           " | ".join(rag_snippets))
    if tool_calls:
        reply_parts.append(
            "It would call " + ", ".join(tc["tool_name"] for tc in tool_calls) +
            " and reply with the confirmed result."
        )
    reply_parts.append(f"Your message: \"{message[:200]}\"")
    reply = " ".join(reply_parts)

    prompt_tokens = _est_tokens(agent.get("system_prompt", ""), message)
    completion_tokens = _est_tokens(reply)
    llm_calls = [{
        "provider": choice["provider"], "model": choice["model"],
        "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
        "cost": 0.0, "latency_ms": int((time.time() - start) * 1000), "stub": True,
    }]
    return {
        "reply": reply,
        "llm_calls": llm_calls,
        "tool_calls": tool_calls,
        "tokens": {"prompt": prompt_tokens, "completion": completion_tokens,
                   "total": prompt_tokens + completion_tokens},
        "cost": 0.0,
        "stub": True,
        "agent_id": agent_id,
        "session_id": session_id,
    }


async def run_agent(spec: dict, message: str, session_id: str,
                    context: dict | None = None) -> dict:
    """Run one user message through the agent described by ``spec``."""
    start = time.time()
    spec = spec or {}
    constraints = dict((spec.get("model_policy") or {}).get("constraints") or {})
    constraints.setdefault("priority", "balanced")
    constraints["require_available"] = True
    choice = select_model(spec.get("description") or spec.get("name") or "chat", constraints)

    agent_key = spec.get("name", "agent")
    session_mem = get_memory("session", agent_key)
    history = await session_mem.get(session_id, limit=10)

    result: dict
    if not provider_available(choice["provider"]):
        result = await _run_stub(spec, message, session_id, context, choice, start)
    else:
        try:
            from .factory.graph_builder import GraphUnavailable, build_graph

            telemetry: dict = {}
            graph = build_graph(spec, telemetry=telemetry)
            msgs: list[tuple[str, str]] = []
            for h in history:
                if h.get("role") in ("user", "assistant") and h.get("content"):
                    msgs.append((("human" if h["role"] == "user" else "ai"), h["content"]))
            msgs.append(("human", message))
            state = await graph.ainvoke({"messages": msgs})
            out_messages = state.get("messages", [])
            reply = ""
            for m in reversed(out_messages):
                content = getattr(m, "content", None)
                if content and getattr(m, "type", "") == "ai":
                    reply = content if isinstance(content, str) else str(content)
                    break
            reply = reply or "(no reply produced)"

            llm_calls = telemetry.get("llm_calls", [])
            prompt_tokens = sum(c.get("prompt_tokens", 0) for c in llm_calls)
            completion_tokens = sum(c.get("completion_tokens", 0) for c in llm_calls)
            if prompt_tokens == 0:
                prompt_tokens = _est_tokens(message)
                completion_tokens = _est_tokens(reply)
            tool_calls = []
            for m in out_messages:
                if getattr(m, "type", "") == "tool":
                    tool_calls.append({
                        "tool_name": getattr(m, "name", "tool"),
                        "input": {}, "output": getattr(m, "content", ""),
                        "duration_ms": 0, "error": None,
                    })
            cost = 0.0
            for c in llm_calls:
                c_tokens = c.get("prompt_tokens", 0) + c.get("completion_tokens", 0)
                c["cost"] = estimate_cost(c.get("model", choice["model"]), c_tokens)
                c["provider"] = c.get("provider", choice["provider"])
                cost += c["cost"]
            result = {
                "reply": reply,
                "llm_calls": llm_calls or [{
                    "provider": choice["provider"], "model": choice["model"],
                    "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
                    "cost": estimate_cost(choice["model"], prompt_tokens + completion_tokens),
                    "latency_ms": int((time.time() - start) * 1000), "stub": False,
                }],
                "tool_calls": tool_calls,
                "tokens": {"prompt": prompt_tokens, "completion": completion_tokens,
                           "total": prompt_tokens + completion_tokens},
                "cost": round(cost or estimate_cost(choice["model"], prompt_tokens + completion_tokens), 6),
                "stub": False,
                "session_id": session_id,
            }
        except Exception:
            # Any live-path failure degrades to the deterministic stub.
            result = await _run_stub(spec, message, session_id, context, choice, start)

    # Persist conversation to session memory (best-effort).
    try:
        await session_mem.append(session_id, {"role": "user", "content": message})
        await session_mem.append(session_id, {"role": "assistant", "content": result["reply"]})
        mem_cfg = spec.get("memory") or {}
        if mem_cfg.get("customer") and context and context.get("customer_id"):
            cust = get_memory("customer", agent_key)
            await cust.append(context["customer_id"], {"last_message": message[:200]})
    except Exception:
        pass
    return result
