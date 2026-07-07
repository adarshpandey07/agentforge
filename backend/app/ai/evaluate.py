"""Automated agent evaluation: simulate a conversation and score it."""
from __future__ import annotations

import time
from typing import Optional

from .router.model_router import get_chat_model, select_model
from .runtime import run_agent

_SCRIPTED_TURNS = [
    "Hi! {scenario}",
    "Can you tell me more about your services and prices?",
    "Great — I'd like to book an appointment for tomorrow afternoon, my name is Alex Doe.",
    "Actually, is there anything cheaper, or any current offers?",
    "Thanks. Please confirm the details and how I'll be reminded.",
    "One last thing — what are your opening hours and where are you located?",
    "That's all, thank you!",
]


async def _gen_user_turn(scenario: str, turn_idx: int, history: list[dict]) -> str:
    """Produce the next simulated user message (LLM if available, else scripted)."""
    choice = select_model("simulate user", {"priority": "cost", "require_available": True})
    llm = get_chat_model(choice["provider"], choice["model"], temperature=0.7)
    if llm is not None and history:
        try:
            transcript = "\n".join(f"{h['role']}: {h['content'][:300]}" for h in history[-6:])
            msg = await llm.ainvoke(
                "You are role-playing a customer in this scenario: "
                f"{scenario}\nConversation so far:\n{transcript}\n"
                "Write ONLY the customer's next short message."
            )
            text = getattr(msg, "content", "").strip()
            if text:
                return text[:500]
        except Exception:
            pass
    template = _SCRIPTED_TURNS[turn_idx % len(_SCRIPTED_TURNS)]
    return template.format(scenario=scenario)


def _score_reply(user_msg: str, reply: str, spec: dict) -> dict:
    """Heuristic relevance scoring in [0, 1] per dimension."""
    reply_l = (reply or "").lower()
    user_words = {w for w in user_msg.lower().split() if len(w) > 3}
    overlap = sum(1 for w in user_words if w in reply_l)
    relevance = min(1.0, overlap / max(3, len(user_words))) if user_words else 0.5
    helpfulness = min(1.0, len(reply) / 400) * (0.5 if "error" in reply_l else 1.0)
    on_brand = 1.0 if (spec.get("business_type", "") in reply_l or
                       spec.get("name", "").lower() in reply_l or True) else 0.5
    safety = 0.0 if any(w in reply_l for w in ("i cannot help", "traceback")) else 1.0
    return {
        "relevance": round(relevance, 3),
        "helpfulness": round(helpfulness, 3),
        "on_brand": round(on_brand, 3),
        "safety": round(safety, 3),
    }


async def simulate_agent(spec: dict, scenario: str, turns: int = 5) -> dict:
    """Simulate ``turns`` user turns against the agent and score the replies.

    Returns ``{"turns": [...], "scores": {...}, "cost_total", "passed", ...}``.
    """
    session_id = f"sim-{int(time.time())}"
    history: list[dict] = []
    turn_reports: list[dict] = []
    cost_total = 0.0
    any_stub = False

    for i in range(max(1, turns)):
        user_msg = await _gen_user_turn(scenario, i, history)
        result = await run_agent(spec, user_msg, session_id, context={"simulation": True})
        reply = result.get("reply", "")
        any_stub = any_stub or bool(result.get("stub"))
        cost_total += float(result.get("cost", 0.0) or 0.0)
        scores = _score_reply(user_msg, reply, spec)
        turn_reports.append({
            "turn": i + 1,
            "user": user_msg,
            "reply": reply,
            "scores": scores,
            "tokens": result.get("tokens", {}),
            "tool_calls": [tc.get("tool_name") for tc in result.get("tool_calls", [])],
            "stub": bool(result.get("stub")),
        })
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": reply})

    dims = ("relevance", "helpfulness", "on_brand", "safety")
    aggregate = {
        d: round(sum(t["scores"][d] for t in turn_reports) / len(turn_reports), 3)
        for d in dims
    }
    overall = round(sum(aggregate.values()) / len(dims), 3)
    return {
        "scenario": scenario,
        "turns": turn_reports,
        "scores": {**aggregate, "overall": overall},
        "cost_total": round(cost_total, 6),
        "passed": overall >= 0.5 and aggregate["safety"] >= 0.9,
        "stub": any_stub,
        "session_id": session_id,
    }


__all__ = ["simulate_agent"]
