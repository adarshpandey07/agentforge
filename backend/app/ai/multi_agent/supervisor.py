"""Supervisor routing for multi-agent specs.

Builds the routing prompt from ``spec.agents`` and routes messages either via
the routed LLM (when a key is configured) or deterministically (keyword match
with round-robin tiebreak).
"""
from __future__ import annotations

import itertools
from typing import Optional

_rr_counters: dict[str, "itertools.cycle"] = {}

# keyword hints per common role id/role text
_ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "booking": ("book", "appointment", "reserve", "reservation", "schedule",
                "reschedule", "cancel", "slot", "availability", "table"),
    "support": ("problem", "issue", "complain", "refund", "broken", "wrong",
                "late", "help", "not working", "angry", "return"),
    "sales": ("price", "cost", "buy", "quote", "package", "membership", "deal",
              "discount", "plan", "interested", "sign up"),
    "marketing": ("offer", "promotion", "newsletter", "coupon", "loyalty"),
    "inventory": ("stock", "available", "in store", "inventory", "size", "quantity"),
    "manager": ("manager", "escalate", "speak to a human", "supervisor"),
    "receptionist": ("hour", "open", "close", "where", "location", "address",
                     "hello", "hi", "menu", "service"),
}


def build_routing_prompt(spec: dict) -> str:
    """Compose the supervisor system prompt from the spec's agents."""
    sup = spec.get("supervisor") or {}
    if sup.get("routing_prompt"):
        base = sup["routing_prompt"]
    else:
        base = (
            f"You are the supervisor for '{spec.get('name', 'the agent team')}'. "
            "Read the user's message and reply with ONLY the id of the single best "
            "team member to handle it."
        )
    lines = [base, "", "Team members:"]
    for a in spec.get("agents", []) or []:
        prompt_head = (a.get("system_prompt") or "")[:140].replace("\n", " ")
        lines.append(f"- {a.get('id')}: {a.get('role', '')} — {prompt_head}")
    lines.append("")
    lines.append("Answer with exactly one id from the list, nothing else.")
    return "\n".join(lines)


def route_deterministic(spec: dict, message: str) -> str:
    """Keyword routing with per-spec round-robin fallback. Always returns an id."""
    agents = spec.get("agents", []) or []
    if not agents:
        return "assistant"
    msg = (message or "").lower()
    best_id, best_hits = None, 0
    for a in agents:
        key = str(a.get("id", "")).lower()
        role = str(a.get("role", "")).lower()
        hits = 0
        for preset, words in _ROLE_KEYWORDS.items():
            if preset in key or preset in role:
                hits += sum(1 for w in words if w in msg)
        # also match agent id/role words appearing directly in the message
        hits += sum(1 for w in key.split("_") + role.split() if w and w in msg)
        if hits > best_hits:
            best_id, best_hits = a["id"], hits
    if best_id:
        return best_id
    # round-robin among agents when nothing matches
    key = spec.get("name", "spec")
    if key not in _rr_counters:
        _rr_counters[key] = itertools.cycle([a["id"] for a in agents])
    return next(_rr_counters[key])


async def route(spec: dict, message: str, history: Optional[list] = None) -> dict:
    """Pick the agent to handle ``message``.

    Returns ``{"agent_id", "method": "llm"|"keyword"|"round_robin"}``.
    """
    agents = spec.get("agents", []) or []
    valid_ids = {a["id"] for a in agents}
    from ..router.model_router import get_chat_model, select_model

    choice = select_model("routing", {"priority": "latency", "require_available": True})
    llm = get_chat_model(choice["provider"], choice["model"], temperature=0)
    if llm is not None and len(valid_ids) > 1:
        try:
            msg = await llm.ainvoke([
                ("system", build_routing_prompt(spec)),
                ("user", message),
            ])
            picked = getattr(msg, "content", "").strip().split()[0].strip(".,'\"")
            if picked in valid_ids:
                return {"agent_id": picked, "method": "llm"}
        except Exception:
            pass
    return {"agent_id": route_deterministic(spec, message), "method": "keyword"}
